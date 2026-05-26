from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
LOG_DIR: Path = _PROJECT_ROOT / "logs"
RUNS_DIR: Path = LOG_DIR / "runs"


def evaluate_run(
    run_dir: Path,
    pending_only: bool = True,
    use_async_batch: bool | None = None,
) -> dict[str, Any]:

    from src.evaluation import OpenAIRagJudge
    from src.evaluation import recompute_llm_eval_metrics
    from src.evaluation import submit_async_batches

    experiments_dir: Path = run_dir / "experiments"
    if not experiments_dir.exists():
        logger.error(
            "[eval] No experiments/ directory found in %s", run_dir
        )
        return {"error": "No experiments directory"}

    exp_paths: list[Path] = _sort_exp_paths(list(experiments_dir.glob("*.json")))
    if not exp_paths:
        logger.warning("[eval] No experiment JSONs found in %s", experiments_dir)
        return {"error": "No experiment JSONs"}

    judge: OpenAIRagJudge = OpenAIRagJudge()


    for exp_path in exp_paths:
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("[eval] Cannot load %s: %s", exp_path, exc)
            continue

        config_name: str = exp_json.get("config_name", exp_path.stem)
        eval_status: str = exp_json.get("evaluation", {}).get("status", "pending")

        if pending_only and eval_status == "completed":
            logger.info(
                "[eval] Config '%s' already fully evaluated, skipping.",
                config_name,
            )
            continue

        logger.info("[eval] Processing config '%s'…", config_name)
        exp_json = judge.evaluate_config_samples(
            experiment_json=exp_json,
            experiment_json_path=exp_path,
            pending_only=pending_only,
        )

        recompute_llm_eval_metrics(exp_json)
        _save_json(exp_json, exp_path)

        logger.info(
            "[eval] Config '%s' evaluation done: status=%s",
            config_name,
            exp_json.get("evaluation", {}).get("status"),
        )


    unresolved: dict[str, list[dict[str, Any]]] = collect_unresolved_eval_items(
        run_dir
    )
    total_unresolved: int = sum(len(v) for v in unresolved.values())

    async_submitted: int = 0
    if total_unresolved > 0:

        if use_async_batch is None:
            try:
                from src.config_loader import get_config
                use_async_batch = (
                    get_config("OPENAI_EVAL_ASYNC_BATCH_FALLBACK", "true").lower()
                    == "true"
                )
            except ImportError:
                import os
                use_async_batch = (
                    os.environ.get(
                        "OPENAI_EVAL_ASYNC_BATCH_FALLBACK", "true"
                    ).lower()
                    == "true"
                )

        if use_async_batch:
            logger.info(
                "[eval] %d unresolved samples across %d configs - submitting "
                "async Batch API jobs.",
                total_unresolved, len(unresolved),
            )
            async_submitted = submit_async_batches(
                unresolved=unresolved, run_dir=run_dir
            )

            still_unresolved = collect_unsubmitted_unresolved(run_dir)
            still_total: int = sum(len(v) for v in still_unresolved.values())
            if still_total > 0:
                logger.warning(
                    "[eval] %d samples remain unresolved and unsubmitted after "
                    "async submission. Run will be marked partial.",
                    still_total,
                )
        else:
            logger.warning(
                "[eval] %d unresolved samples found. Async fallback is disabled. "
                "Mark run as partial. Run with --use-async-batch to submit them.",
                total_unresolved,
            )


    summary_path: Path = regenerate_summary_for_run(run_dir)
    logger.info("[eval] Summary saved: %s", summary_path)


    _update_manifest_eval_status(run_dir)


    return _build_run_counts(run_dir, async_submitted)


def collect_unresolved_eval_items(
    run_dir: Path,
) -> dict[str, list[dict[str, Any]]]:

    unresolved_statuses: frozenset[str] = frozenset({
        "pending", "retry_pending", "failed", "error"
    })
    result: dict[str, list[dict[str, Any]]] = {}
    run_id: str = run_dir.name

    experiments_dir: Path = run_dir / "experiments"
    if not experiments_dir.exists():
        return result

    for exp_path in _sort_exp_paths(list(experiments_dir.glob("*.json"))):
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("[eval] Cannot load %s: %s", exp_path, exc)
            continue

        config_name: str = exp_json.get("config_name", exp_path.stem)
        items: list[dict[str, Any]] = []

        for i, sample in enumerate(exp_json.get("samples", [])):
            ev: dict[str, Any] = sample.get("eval") or {}
            status: str = ev.get("status", "pending")
            if status not in unresolved_statuses:
                continue
            items.append({
                "run_id": run_id,
                "config_name": config_name,
                "experiment_json_path": str(exp_path),
                "sample_index": i,
                "eval_item_id": sample.get("eval_item_id", ""),
                "question": sample.get("question", ""),
                "answer": sample.get("answer", ""),
                "ground_truth": sample.get("ground_truth", ""),
                "contexts": sample.get("contexts", []),
                "previous_status": status,
                "attempt_count": ev.get("attempt_count", 0),
                "last_error": ev.get("last_error"),
            })

        if items:
            result[config_name] = items
            logger.info(
                "[audit] Config '%s': %d unresolved sample(s).",
                config_name, len(items),
            )

    total: int = sum(len(v) for v in result.values())
    if total == 0:
        logger.info("[audit] All samples resolved - no Batch API jobs needed.")
    else:
        logger.info(
            "[audit] %d total unresolved sample(s) across %d config(s).",
            total, len(result),
        )
    return result


def collect_unsubmitted_unresolved(
    run_dir: Path,
) -> dict[str, list[dict[str, Any]]]:

    in_progress: frozenset[str] = frozenset({
        "batch_submitted", "batch_running", "completed"
    })
    unresolved_statuses: frozenset[str] = frozenset({
        "pending", "retry_pending", "failed", "error"
    })
    result: dict[str, list[dict[str, Any]]] = {}
    run_id: str = run_dir.name

    experiments_dir: Path = run_dir / "experiments"
    if not experiments_dir.exists():
        return result

    for exp_path in _sort_exp_paths(list(experiments_dir.glob("*.json"))):
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("[eval] Cannot load %s: %s", exp_path, exc)
            continue

        config_name: str = exp_json.get("config_name", exp_path.stem)
        items: list[dict[str, Any]] = []

        for i, sample in enumerate(exp_json.get("samples", [])):
            ev: dict[str, Any] = sample.get("eval") or {}
            status: str = ev.get("status", "pending")
            if status in in_progress:
                continue
            if status not in unresolved_statuses:
                continue
            items.append({
                "run_id": run_id,
                "config_name": config_name,
                "experiment_json_path": str(exp_path),
                "sample_index": i,
                "eval_item_id": sample.get("eval_item_id", ""),
                "question": sample.get("question", ""),
                "answer": sample.get("answer", ""),
                "ground_truth": sample.get("ground_truth", ""),
                "contexts": sample.get("contexts", []),
                "previous_status": status,
                "attempt_count": ev.get("attempt_count", 0),
                "last_error": ev.get("last_error"),
            })

        if items:
            result[config_name] = items
            logger.warning(
                "[audit2] Config '%s': %d sample(s) still unresolved and "
                "not submitted to a batch job.",
                config_name, len(items),
            )

    total: int = sum(len(v) for v in result.values())
    if total == 0:
        logger.info("[audit2] All samples are either completed or in a batch job.")
    else:
        logger.warning(
            "[audit2] %d sample(s) across %d config(s) are unresolved and "
            "NOT in any batch job. Run will be marked partial.",
            total, len(result),
        )
    return result


def regenerate_summary_for_run(run_dir: Path) -> Path:

    from src.evaluation.schemas import PERFORMANCE_METRIC_NAMES

    run_id: str = run_dir.name
    experiments_dir: Path = run_dir / "experiments"
    summaries_dir: Path = run_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)


    manifest_data: dict[str, Any] = {}
    manifest_path: Path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass


    experiments_block: dict[str, Any] = {}
    for exp_path in _sort_exp_paths(list(experiments_dir.glob("*.json"))):
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("[summary] Cannot load %s: %s", exp_path, exc)
            continue

        config_name: str = exp_json.get("config_name", exp_path.stem)
        eval_block: dict[str, Any] = exp_json.get("evaluation", {})
        n_total: int = eval_block.get("num_samples_total", 0)
        n_evaluated: int = eval_block.get("num_samples_evaluated", 0)
        n_pending: int = eval_block.get("num_samples_pending", 0)
        n_failed: int = eval_block.get("num_samples_failed", 0)
        eval_status: str = eval_block.get("status", "pending")
        eval_method: str | None = eval_block.get("method")
        eval_model: str | None = eval_block.get("model")


        perf_metrics: dict[str, float] = {}
        quality_metrics: dict[str, float] = {}
        for m in exp_json.get("metrics", []):
            metric_name: str = m.get("metric", "")
            value: float = float(m.get("value", 0.0))
            if metric_name in PERFORMANCE_METRIC_NAMES:
                perf_metrics[metric_name] = round(value, 4)
            elif m.get("method") == "openai_llm_judge":
                quality_metrics[metric_name] = round(value, 4)

        n_queries: int = exp_json.get("num_queries", 0)
        experiments_block[config_name] = {
            "config_option": exp_json.get("config_option", 0),
            "status": "completed",
            "elapsed_seconds": round(float(exp_json.get("elapsed_seconds", 0.0)), 3),
            "elapsed_human": exp_json.get("elapsed_human", ""),
            "num_queries": n_queries,
            "performance_metrics": perf_metrics,
            "quality_metrics": quality_metrics,
            "eval_pending_count": n_pending,
            "eval_failed_count": n_failed,
            "evaluation_status": eval_status,
            "evaluation_method": eval_method,
            "evaluation_model": eval_model,
        }


    all_statuses: list[str] = [
        v.get("evaluation_status", "pending")
        for v in experiments_block.values()
    ]
    if all(s == "completed" for s in all_statuses):
        overall_eval_status: str = "completed"
    elif any(s == "evaluation_in_progress" for s in all_statuses):
        overall_eval_status = "evaluation_in_progress"
    elif any(s in ("completed", "partial") for s in all_statuses):
        overall_eval_status = "partial"
    else:
        overall_eval_status = "pending"


    total_samples: int = sum(
        v.get("num_queries", 0) for v in experiments_block.values()
    )
    evaluated_samples: int = sum(

        int(v.get("num_queries", 0))
        - int(v.get("eval_pending_count", 0))
        - int(v.get("eval_failed_count", 0))
        for v in experiments_block.values()
    )
    pending_total: int = sum(
        int(v.get("eval_pending_count", 0)) for v in experiments_block.values()
    )
    eval_completion_rate: float = (
        round((evaluated_samples / total_samples) * 100.0, 2)
        if total_samples else 0.0
    )


    eval_methods: list[str] = [
        v["evaluation_method"] for v in experiments_block.values()
        if v.get("evaluation_method")
    ]
    eval_models: list[str] = [
        v["evaluation_model"] for v in experiments_block.values()
        if v.get("evaluation_model")
    ]

    timestamp_start: str = manifest_data.get(
        "created_at",
        datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    )
    timestamp_end: str = manifest_data.get(
        "updated_at",
        datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    )

    summary: dict[str, Any] = {
        "schema_version": "2.0",
        "report_type": "experiment_summary",
        "run_id": run_id,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "total_elapsed_seconds": round(
            sum(
                float(v.get("elapsed_seconds", 0.0))
                for v in experiments_block.values()
            ),
            3,
        ),
        "total_elapsed_human": _format_duration(
            sum(
                float(v.get("elapsed_seconds", 0.0))
                for v in experiments_block.values()
            )
        ),
        "mode": manifest_data.get("mode", ""),
        "dataset": manifest_data.get("dataset", ""),
        "model_label": manifest_data.get("model_label", ""),
        "model_detected": manifest_data.get("model_detected", ""),
        "model_size_gb": manifest_data.get("model_size_gb", ""),
        "model_size_category": manifest_data.get("model_size_category", ""),
        "evaluation": {
            "status": overall_eval_status,
            "method": eval_methods[0] if eval_methods else None,
            "model": eval_models[0] if eval_models else None,
            "scores_scale": "0_to_100",
            "num_samples_total": total_samples,
            "num_samples_evaluated": evaluated_samples,
            "num_samples_pending": pending_total,
            "eval_completion_rate": eval_completion_rate,
        },
        "experiments": experiments_block,
    }


    _RUN_TYPE_TO_FAMILY: dict[str, str] = {
        "main": "main_experiment",
        "model_selection": "model_selection",
    }
    _raw_family: str = str(manifest_data.get("experiment_family", "") or "").strip()
    if not _raw_family:
        _run_type: str = str(manifest_data.get("run_type", "main") or "main").strip()
        _raw_family = _RUN_TYPE_TO_FAMILY.get(_run_type, "main_experiment")
    summary["experiment_family"] = _raw_family
    summary["experiment_stage"] = manifest_data.get("experiment_stage", "")
    summary["combo_alias"] = manifest_data.get("combo_alias", "")
    summary["combo_retrieval_model"] = (
            manifest_data.get("combo_retrieval_model")
            or manifest_data.get("retrieval_model", "")
    )
    summary["combo_reranker_model"] = (
            manifest_data.get("combo_reranker_model")
            or manifest_data.get("reranker_model", "")
    )


    for key in (
        "experiment_family",
        "experiment_stage",
        "combo_alias",
        "retrieval_model",
        "reranker_model",
        "llm_label",
    ):
        value = manifest_data.get(key)
        if value not in (None, ""):
            summary[key] = value


    summary_path: Path = summaries_dir / "experiment_summary.json"
    _save_json(summary, summary_path)


    _write_human_summary(summary, summaries_dir / "experiment_summary_human.md")


    top_summaries: Path = LOG_DIR / "summaries"
    top_summaries.mkdir(parents=True, exist_ok=True)
    top_json: Path = top_summaries / f"{run_id}__experiment_summary.json"
    try:
        import shutil
        shutil.copy2(summary_path, top_json)
        shutil.copy2(
            summaries_dir / "experiment_summary_human.md",
            top_summaries / f"{run_id}__experiment_summary_human.md",
        )
    except OSError as exc:
        logger.warning("[summary] Could not copy to top-level summaries: %s", exc)

    logger.info("[summary] Regenerated: %s", summary_path)
    return summary_path


def _sort_exp_paths(paths: list[Path]) -> list[Path]:

    no_rag: list[Path] = [p for p in paths if p.stem == "no_rag"]
    rest: list[Path] = sorted(p for p in paths if p.stem != "no_rag")
    return no_rag + rest


def _update_manifest_eval_status(run_dir: Path) -> None:

    manifest_path: Path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        return
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest: dict[str, Any] = json.load(f)
    except (OSError, json.JSONDecodeError):
        return

    experiments_dir: Path = run_dir / "experiments"
    for config_name, config_entry in manifest.get("experiments", {}).items():
        exp_path: Path = experiments_dir / f"{config_name}.json"
        if not exp_path.exists():
            continue
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
            config_entry["evaluation_status"] = (
                exp_json.get("evaluation", {}).get("status", "pending")
            )
        except (OSError, json.JSONDecodeError):
            pass


    all_eval_statuses: list[str] = [
        e.get("evaluation_status", "pending")
        for e in manifest.get("experiments", {}).values()
    ]
    if all(s == "completed" for s in all_eval_statuses):
        manifest["status"] = "completed"
    elif any(
        s in ("completed", "partial") for s in all_eval_statuses
    ):
        manifest["status"] = "experiments_completed_evaluation_partial"
    else:
        manifest["status"] = "experiments_completed_evaluation_pending"

    manifest["updated_at"] = datetime.datetime.now().strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    _save_json(manifest, manifest_path)


def _build_run_counts(
    run_dir: Path, async_submitted: int
) -> dict[str, Any]:

    experiments_dir: Path = run_dir / "experiments"
    total: int = 0
    completed: int = 0
    pending: int = 0
    failed: int = 0

    for exp_path in experiments_dir.glob("*.json"):
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for s in exp_json.get("samples", []):
            total += 1
            status: str = (s.get("eval") or {}).get("status", "pending")
            if status == "completed":
                completed += 1
            elif status in ("pending", "retry_pending", "batch_submitted",
                           "batch_running"):
                pending += 1
            else:
                failed += 1

    print()
    print("=" * 70)
    print(f"  EVALUATION SUMMARY - run_id={run_dir.name}")
    print("=" * 70)
    print(f"  Total samples:     {total}")
    print(f"  Completed:         {completed}")
    print(f"  Pending / in-batch:{pending}")
    print(f"  Failed:            {failed}")
    print(f"  Async jobs submitted: {async_submitted}")
    completion: float = (completed / total * 100.0) if total else 0.0
    print(f"  Completion rate:   {completion:.1f}%")
    print("=" * 70)
    print()

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "async_submitted": async_submitted,
        "completion_rate": round(completion, 2),
    }


def _save_json(data: dict[str, Any], path: Path) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _format_duration(seconds: float | None) -> str:

    if not seconds or seconds < 0:
        return "0s"
    total: int = int(round(float(seconds)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _write_human_summary(
    summary: dict[str, Any], path: Path
) -> None:

    run_id: str = summary.get("run_id", "?")
    eval_status: str = summary.get("evaluation", {}).get("status", "?")
    eval_model: str = summary.get("evaluation", {}).get("model") or "-"
    n_eval: int = summary.get("evaluation", {}).get("num_samples_evaluated", 0)
    n_total: int = summary.get("evaluation", {}).get("num_samples_total", 0)
    completion: float = summary.get("evaluation", {}).get(
        "eval_completion_rate", 0.0
    )

    lines: list[str] = [
        f"# Resumen de evaluación `{run_id}`",
        "",
        f"- Inicio: `{summary.get('timestamp_start', '-')}`",
        f"- Fin: `{summary.get('timestamp_end', '-')}`",
        f"- Dataset: `{summary.get('dataset', '-')}`",
        f"- Modo: `{summary.get('mode', '-')}`",
        f"- Modelo pipeline: `{summary.get('model_label', '-')}`",
        f"- Estado de evaluación: **{eval_status}**",
        f"- Juez LLM: `{eval_model}`",
        f"- Muestras evaluadas: {n_eval}/{n_total} ({completion:.1f}%)",
        "",
        "## Configuraciones",
        "",
        "| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |",
        "|---|---|---|---|---|---|",
    ]
    for name, info in summary.get("experiments", {}).items():
        qm: dict[str, float] = info.get("quality_metrics", {})
        pm: dict[str, float] = info.get("performance_metrics", {})
        lines.append(
            f"| `{name}` | {info.get('evaluation_status', '?')} | "
            f"{info.get('num_queries', 0)} | "
            f"{qm.get('correctness_mean', 0.0):.1f} | "
            f"{qm.get('faithfulness_mean', 0.0):.1f} | "
            f"{pm.get('latency_mean_ms', 0.0):.1f} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _find_latest_run_dir() -> Path | None:

    if not RUNS_DIR.exists():
        return None
    run_dirs: list[Path] = sorted(
        [d for d in RUNS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )
    return run_dirs[-1] if run_dirs else None


def _find_run_dir_by_id(run_id: str) -> Path | None:

    candidate: Path = RUNS_DIR / run_id
    if candidate.exists():
        return candidate

    matches: list[Path] = [
        d for d in RUNS_DIR.iterdir()
        if d.is_dir() and run_id in d.name
    ]
    return matches[0] if len(matches) == 1 else None


def _all_run_dirs() -> list[Path]:

    if not RUNS_DIR.exists():
        return []
    return sorted(d for d in RUNS_DIR.iterdir() if d.is_dir())


def main(argv: list[str] | None = None) -> int:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Phase 2 evaluation - OpenAI LLM judge for RAG thesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.evaluation.run_evaluation --latest
  python -m src.evaluation.run_evaluation --all-runs --regenerate-summary
  python -m src.evaluation.run_evaluation --all-runs --all-samples
  python -m src.evaluation.run_evaluation --run-id run_20260512_193621_unknown_878aaf0a
  python -m src.evaluation.run_evaluation --run-dir logs/runs/run_20260512_193621_unknown_878aaf0a
  python -m src.evaluation.run_evaluation --latest --pending-only
  python -m src.evaluation.run_evaluation --latest --use-async-batch
  python -m src.evaluation.run_evaluation --latest --poll-batches
  python -m src.evaluation.run_evaluation --latest --regenerate-summary
        """,
    )


    sel = parser.add_mutually_exclusive_group()
    sel.add_argument(
        "--run-id", type=str, default=None,
        help="Run ID to evaluate (e.g. run_20260512_193621_unknown_878aaf0a).",
    )
    sel.add_argument(
        "--latest", action="store_true",
        help="Evaluate the most recent run.",
    )
    sel.add_argument(
        "--run-dir", type=str, default=None,
        help="Direct path to a run directory.",
    )
    sel.add_argument(
        "--all-runs", action="store_true",
        help=(
            "Process every run directory under logs/runs/ in chronological "
            "order. Combines with --regenerate-summary, --all-samples, "
            "--poll-batches etc. exactly as single-run mode does."
        ),
    )


    parser.add_argument(
        "--pending-only", action="store_true", default=True,
        help="Evaluate only pending/retry_pending samples (default: True).",
    )
    parser.add_argument(
        "--all-samples", action="store_true",
        help="Re-evaluate all samples (overrides --pending-only).",
    )
    parser.add_argument(
        "--use-async-batch", action="store_true",
        help="Submit unresolved samples to Batch API after sync evaluation.",
    )
    parser.add_argument(
        "--poll-batches", action="store_true",
        help="Poll existing Batch API jobs and process completed results.",
    )
    parser.add_argument(
        "--regenerate-summary", action="store_true",
        help="Only regenerate the summary without evaluating.",
    )

    args: argparse.Namespace = parser.parse_args(argv)


    run_dirs: list[Path] = []

    if args.all_runs:
        run_dirs = _all_run_dirs()
        if not run_dirs:
            print(f"ERROR: No run directories found under {RUNS_DIR}.", file=sys.stderr)
            return 1
        logger.info("--all-runs: processing %d run(s).", len(run_dirs))
    else:
        run_dir: Path | None = None
        if args.run_dir:
            run_dir = Path(args.run_dir).resolve()
        elif args.run_id:
            run_dir = _find_run_dir_by_id(args.run_id)
        elif args.latest:
            run_dir = _find_latest_run_dir()

        if run_dir is None:
            print(
                "ERROR: Could not determine run directory. "
                "Use --run-id, --latest, --run-dir, or --all-runs.",
                file=sys.stderr,
            )
            return 1

        if not run_dir.exists():
            print(f"ERROR: Run directory not found: {run_dir}", file=sys.stderr)
            return 1

        run_dirs = [run_dir]


    errors: int = 0
    for run_dir in run_dirs:
        if not run_dir.exists():
            logger.warning("Run directory not found, skipping: %s", run_dir)
            errors += 1
            continue

        logger.info("Run directory: %s", run_dir)


        if args.poll_batches:
            from src.evaluation import poll_async_batches
            result: dict[str, Any] = poll_async_batches(run_dir)
            logger.info("Poll result: %s", result)
            if result.get("completed", 0) > 0 or result.get("checked", 0) > 0:
                _recompute_all_metrics(run_dir)
                regenerate_summary_for_run(run_dir)
                _update_manifest_eval_status(run_dir)
            continue


        if args.regenerate_summary:
            summary_path: Path = regenerate_summary_for_run(run_dir)
            _update_manifest_eval_status(run_dir)
            logger.info("Summary regenerated: %s", summary_path)
            continue


        pending_only: bool = not args.all_samples
        use_async: bool | None = True if args.use_async_batch else None
        evaluate_run(
            run_dir=run_dir,
            pending_only=pending_only,
            use_async_batch=use_async,
        )

    return 0 if errors == 0 else 1


def _recompute_all_metrics(run_dir: Path) -> None:

    from src.evaluation import recompute_llm_eval_metrics
    experiments_dir: Path = run_dir / "experiments"
    for exp_path in experiments_dir.glob("*.json"):
        try:
            with open(exp_path, encoding="utf-8") as f:
                exp_json: dict[str, Any] = json.load(f)
            recompute_llm_eval_metrics(exp_json)
            _save_json(exp_json, exp_path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("[eval] Cannot process %s: %s", exp_path, exc)


if __name__ == "__main__":
    sys.exit(main())


__all__: list[str] = [
    "evaluate_run",
    "collect_unresolved_eval_items",
    "collect_unsubmitted_unresolved",
    "regenerate_summary_for_run",
]
