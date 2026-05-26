from __future__ import annotations

import argparse
import copy
import csv
import json
import logging
import statistics
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing_extensions import deprecated


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


sys.path.insert(0, str(_PROJECT_ROOT))


LOG_DIR: Path = _PROJECT_ROOT / "logs"


OUTPUT_DIR: Path = _PROJECT_ROOT / "output" / "comparison"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


logger: logging.Logger = logging.getLogger(__name__)


RETRIEVAL_MODELS: list[str] = [
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
]


RERANKER_MODELS: list[str] = [
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "BAAI/bge-reranker-base",
]


COMBO_ALIASES: dict[str, str] = {
    "BAAI/bge-base-en-v1.5":                           "bge-base",
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1": "multi-qa-mini",
    "cross-encoder/ms-marco-MiniLM-L-12-v2":           "ms-marco-L12",
    "cross-encoder/ms-marco-MiniLM-L-6-v2":            "ms-marco-L6",
    "BAAI/bge-reranker-base":                          "bge-reranker",
    "none":                                            "no-reranker",
}


EXPERIMENT_FAMILY: str = "combo_sweep"
EXPERIMENT_STAGE: str = "step_1_combo_selection"


COMBO_SELECTION_CONFIGS: list[str] = [
    "baseline_s_rr",
    "baseline_s_rr_grounded",
    "optimized_s_rr",
    "optimized_s_rr_grounded",
]


QUALITY_WEIGHTS: dict[str, float] = {
    "correctness_mean": 0.35,
    "faithfulness_mean": 0.35,
    "context_support_mean": 0.20,
    "answer_relevance_mean": 0.10,
}


DEFAULT_COMPARISON_CONFIGS: list[int] = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
]


DEFAULT_MAX_SAMPLES: int = 5


COMPARISON_DATASET: str = "triviaqa"


def _dfmt(value: float, decimals: int = 2) -> str:

    return f"{value:.{decimals}f}".replace(".", ",")


def _es_yformatter(x: float, _pos: int) -> str:

    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.2f}".replace(".", ",")


def _latex_escape(text: Any) -> str:

    s: str = str(text)
    replacements: dict[str, str] = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def _safe_path_label(text: Any) -> str:

    s = str(text or "unknown").strip()
    replacements = {
        ":": "_",
        "/": "_",
        "\\": "_",
        " ": "_",
        "@": "_",
        "*": "_",
        "?": "_",
        '"': "_",
        "<": "_",
        ">": "_",
        "|": "_",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "unknown"


def _summary_llm_label(summary: dict[str, Any], combo_alias: str = "") -> str:

    detected: str = str(summary.get("model_detected", "") or "").strip()
    if detected:
        return detected

    label: str = str(summary.get("model_label", "") or "").strip()
    if label and combo_alias and label.endswith(f"__{combo_alias}"):
        label = label[: -(len(combo_alias) + 2)]
    if label:
        return label

    model: str = str(summary.get("model", "") or "").strip()
    return model or "unknown"


def _cross_combo_metadata(combos: list[ComboSpec]) -> tuple[str, str]:

    datasets: set[str] = set()
    llms: set[str] = set()

    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue

        dataset: str = str(summary.get("dataset", "") or "").strip()
        if dataset:
            datasets.add(dataset)

        llm_label: str = _summary_llm_label(summary, combo.alias)
        if llm_label:
            llms.add(llm_label)

    dataset_label: str
    if len(datasets) == 1:
        dataset_label = next(iter(datasets))
    elif len(datasets) > 1:
        dataset_label = "mixed: " + ", ".join(sorted(datasets))
    else:
        dataset_label = "unknown"

    llm_display: str
    if len(llms) == 1:
        llm_display = next(iter(llms))
    elif len(llms) > 1:
        llm_display = "mixed: " + ", ".join(sorted(llms))
    else:
        llm_display = "unknown"

    return dataset_label, llm_display


@dataclass
class ComboSpec:


    retrieval_model: str
    reranker_model: str
    alias: str = field(default="", init=False)
    run_id: str = field(default="", init=False)
    run_dir: Path | None = field(default=None, init=False)
    success: bool = field(default=False, init=False)
    error_message: str = field(default="", init=False)

    def __post_init__(self) -> None:
        r_alias: str = COMBO_ALIASES.get(
            self.retrieval_model, self.retrieval_model.split("/")[-1]
        )
        rr_alias: str = COMBO_ALIASES.get(
            self.reranker_model, self.reranker_model.split("/")[-1]
        )
        self.alias = f"{r_alias}__{rr_alias}"

    def label(self) -> str:

        return self.alias


def build_combo_configs(
    retrieval_model: str,
    reranker_model: str,
) -> dict[str, dict[str, Any]]:

    from src.pipeline import PIPELINE_CONFIGS as _base_configs

    configs: dict[str, dict[str, Any]] = copy.deepcopy(_base_configs)

    for cfg_name, cfg in configs.items():

        if cfg.get("retriever") == "faiss" and cfg.get("embedder") not in (
            "none", None
        ):
            cfg["embedder"] = retrieval_model


        if cfg.get("reranker") not in ("none", None):
            if reranker_model == "none":

                cfg["reranker"] = "none"
                cfg.pop("reranker_top_n", None)

                cfg["top_k"] = 5
            else:
                cfg["reranker"] = reranker_model

    return configs


def _format_error_report(
    context: str,
    exc: BaseException,
    tb_str: str = "",
) -> str:

    lines: list[str] = [
        f"ERROR in: {context}",
        f"  Type   : {type(exc).__qualname__}",
        f"  Message: {exc}",
        f"  Cause  : {exc.__cause__ or exc.__context__ or '(none)'}",
    ]
    if tb_str:
        lines.append("  Traceback (most recent call last):")
        for tb_line in tb_str.strip().splitlines():
            lines.append(f"    {tb_line}")
    return "\n".join(lines)


def _write_experiment_family_metadata(
    run_dir: Path,
    family: str,
    stage: str,
    combo_alias: str,
    retrieval_model: str,
    reranker_model: str,
    dataset: str,
    llm_label: str,
) -> None:

    metadata: dict[str, Any] = {
        "experiment_family": family,
        "experiment_stage": stage,
        "combo_alias": combo_alias,
        "retrieval_model": retrieval_model,
        "reranker_model": reranker_model,
        "dataset": dataset,
        "llm_label": llm_label,
    }

    path: Path = run_dir / "artifact_metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_combo(
    combo: ComboSpec,
    configs: list[int],
    max_samples: int,
    dry_run: bool,
    dataset: str,
    model_label: str,
    cache_manager: Any = None,
    cached_only: bool = False,
) -> ComboSpec:

    import src.pipeline as _pipeline_module
    from src.evaluation import (
        ExperimentRunner,
        ExperimentLogV2,
        RunManifest,
        create_run_id,
    )
    from scripts.run_experiments import (
        EXPERIMENT_ORDER,
        DISABLED_CONFIGS,
        DATASET_CORPUS_MAPPING,
        _phase1_run_dirs,
        _create_dry_run_pipeline,
        _check_server_alive,
        preflight_get_active_model,
        ExperimentResult,
    )
    from src.pipeline import RAGPipeline, CORPUS_DIR as _CORPUS_DIR
    from src.dataset_manager import DatasetManager


    combo_tag: str = combo.alias.replace("/", "-")
    run_id: str = create_run_id(
        f"{model_label}__{combo_tag}" if model_label else combo_tag
    )
    combo.run_id = run_id

    logger.info("=" * 70)
    logger.info("  COMBO: %s", combo.alias)
    logger.info("  retrieval_model: %s", combo.retrieval_model)
    logger.info("  reranker_model:  %s", combo.reranker_model)
    logger.info("  run_id:          %s", run_id)
    logger.info("=" * 70)


    dynamic_configs: dict[str, dict[str, Any]] = build_combo_configs(
        retrieval_model=combo.retrieval_model,
        reranker_model=combo.reranker_model,
    )


    _original_pipeline_configs: dict[str, dict[str, Any]] = (
        _pipeline_module.PIPELINE_CONFIGS
    )
    _original_retrieval_model: str = _pipeline_module.RETRIEVAL_MODEL
    _original_reranker_model: str = _pipeline_module.RERANKER_MODEL

    try:
        _pipeline_module.PIPELINE_CONFIGS = dynamic_configs
        _pipeline_module.RETRIEVAL_MODEL = combo.retrieval_model
        _pipeline_module.RERANKER_MODEL = (
            combo.reranker_model if combo.reranker_model != "none" else ""
        )


        dataset_info: dict = DATASET_CORPUS_MAPPING.get(dataset, {})
        corpus_dir: Path = dataset_info.get("corpus_dir", _CORPUS_DIR)
        corpus_prefixes: list[str] | None = dataset_info.get("corpus_prefixes", None)

        mgr: DatasetManager = DatasetManager()
        samples = mgr.load(dataset, max_samples=max_samples,
                           allow_eval_rebuild=not cached_only)
        queries: list[str] = [s.question for s in samples]
        ground_truths: list[str] = [s.answer for s in samples]

        from src.cache import query_id_for as _qid
        query_ids: list[str] = [_qid(q) for q in queries]

        if not dry_run:


            detected_model_meta: dict[str, Any] = (
                preflight_get_active_model() or {}
            )
        else:
            detected_model_meta = {}


        llm_label: str = (
            model_label
            or detected_model_meta.get("actual_model", "")
            or detected_model_meta.get("model", "")
        )

        llm_label_safe: str = (
            llm_label.replace(":", "_").replace("/", "_") if llm_label else ""
        )
        combined_label: str = (
            f"{llm_label_safe}__{combo.alias}"
            if llm_label_safe else combo.alias
        )

        run_dir, experiments_dir, _ = _phase1_run_dirs(run_id)
        combo.run_dir = run_dir

        manifest: RunManifest = RunManifest(
            run_id=run_id,
            run_dir=run_dir,
            dataset=dataset,
            mode="dry_run" if dry_run else "real",
            model_label=combined_label,
            model_detected=(
                detected_model_meta.get("actual_model", "")
                or detected_model_meta.get("model", "")
            ),
            model_size_gb=str(detected_model_meta.get("model_size_gb", "")),
            model_size_category=detected_model_meta.get("model_size_category", ""),
            num_configs_expected=len(configs),
            num_queries_per_config=len(samples),
        )


        manifest._data["experiment_family"] = EXPERIMENT_FAMILY
        manifest._data["experiment_stage"] = EXPERIMENT_STAGE
        manifest._data["combo_alias"] = combo.alias
        manifest._data["retrieval_model"] = combo.retrieval_model
        manifest._data["reranker_model"] = combo.reranker_model
        manifest._data["llm_label"] = llm_label_safe or "unknown"
        manifest.save()


        _write_experiment_family_metadata(
            run_dir=run_dir,
            family=EXPERIMENT_FAMILY,
            stage=EXPERIMENT_STAGE,
            combo_alias=combo.alias,
            retrieval_model=combo.retrieval_model,
            reranker_model=combo.reranker_model,
            dataset=dataset,
            llm_label=llm_label_safe or "unknown",
        )

        ordered: list[tuple[int, str]] = [
            (opt, name) for opt, name in EXPERIMENT_ORDER
            if opt in configs and name not in DISABLED_CONFIGS
        ]

        results: list[ExperimentResult] = []
        invalid_count: int = 0

        for config_option, config_name in ordered:
            if config_name not in dynamic_configs:
                logger.warning("Config '%s' not in dynamic_configs, skipping.", config_name)
                continue

            config: dict[str, Any] = dict(dynamic_configs[config_name])
            config["mode"] = "dry_run" if dry_run else "real"

            config["combo_retrieval_model"] = combo.retrieval_model
            config["combo_reranker_model"] = combo.reranker_model

            ts_start_iso: str = time.strftime("%Y-%m-%dT%H:%M:%S")
            t_start: float = time.perf_counter()

            try:
                if not dry_run and not _check_server_alive(timeout=10):
                    raise ConnectionError(
                        f"Server not reachable before config '{config_name}'. "
                        "Check the SSH reverse tunnel."
                    )

                if dry_run:
                    pipeline = _create_dry_run_pipeline(
                        config_option, config_name, config
                    )
                else:
                    pipeline = RAGPipeline(config_option=config_option)

                if config_name != "no_rag":
                    if cache_manager is not None and not dry_run:
                        pipeline.attach_cache(
                            cache_manager,
                            query_ids=dict(zip(queries, query_ids)),
                            cached_only=cached_only,
                            dataset_name=dataset,
                        )
                    pipeline.build_index(
                        corpus_dir=corpus_dir,
                        persist_index=False,
                        corpus_file_prefixes=corpus_prefixes,
                    )
                else:
                    pipeline.is_indexed = True

                from src.pipeline import PipelineResult
                pipeline_results: list[PipelineResult] = pipeline.run_batch(
                    queries, query_ids=query_ids,
                )

                elapsed: float = time.perf_counter() - t_start
                ts_end_iso: str = time.strftime("%Y-%m-%dT%H:%M:%S")

                runner: ExperimentRunner = ExperimentRunner(log_dir=LOG_DIR)
                log_v2: ExperimentLogV2 = runner.run_collect_only(
                    results=pipeline_results,
                    config_name=config_name,
                    config_option=config_option,
                    config=config,
                    run_id=run_id,
                    dataset=dataset,
                    ground_truths=ground_truths,
                    timestamp_start=ts_start_iso,
                    timestamp_end=ts_end_iso,
                    elapsed_seconds=elapsed,
                )

                er: ExperimentResult = ExperimentResult(
                    config_option=config_option,
                    config_name=config_name,
                    pipeline_results=pipeline_results,
                    elapsed_seconds=elapsed,
                    success=True,
                    experiment_log_v2=log_v2,
                )
                results.append(er)
                log_v2.save(experiments_dir)

            except (ConnectionError, TimeoutError, ImportError,
                    FileNotFoundError, RuntimeError, ValueError) as exc:
                elapsed = time.perf_counter() - t_start
                tb_str: str = traceback.format_exc()
                err_report: str = _format_error_report(
                    f"combo={combo.alias} config={config_name}",
                    exc,
                    tb_str,
                )
                logger.error("%s", err_report)
                er = ExperimentResult(
                    config_option=config_option,
                    config_name=config_name,
                    pipeline_results=[],
                    elapsed_seconds=elapsed,
                    success=False,
                    error_message=str(exc),
                )
                results.append(er)

            manifest.update_config_completed(
                config_name=er.config_name,
                config_option=er.config_option,
                elapsed_seconds=er.elapsed_seconds,
                success=er.success,
                error_message=er.error_message,
            )

            if not er.success and (
                "no devolvió un nombre de modelo" in (er.error_message or "")
                or "did not return a model name" in (er.error_message or "")
                or "no model name returned" in (er.error_message or "")
            ):
                invalid_count += 1
                if invalid_count > 2:
                    logger.error(
                        "[combo %s] Cancelling batch: too many invalid experiments.",
                        combo.alias,
                    )
                    break

        manifest.mark_run_evaluation_pending()
        combo.success = any(er.success for er in results)
        logger.info(
            "[combo %s] Done: %d/%d configs succeeded.",
            combo.alias,
            sum(er.success for er in results),
            len(results),
        )

    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        tb_str = traceback.format_exc()
        err_report = _format_error_report(
            f"combo setup: {combo.alias}",
            exc,
            tb_str,
        )
        logger.error("%s", err_report)
        combo.success = False
        combo.error_message = str(exc)

    finally:

        _pipeline_module.PIPELINE_CONFIGS = _original_pipeline_configs
        _pipeline_module.RETRIEVAL_MODEL = _original_retrieval_model
        _pipeline_module.RERANKER_MODEL = _original_reranker_model

    return combo


def evaluate_all_combos(
    combos: list[ComboSpec],
    dry_run: bool = False,
) -> dict[str, dict[str, Any]]:

    from scripts.run_experiments import _ensure_metrics_and_summary

    if dry_run:
        logger.info("[eval] Dry-run - skipping evaluation for all combos.")
        return {}

    try:
        from src.config_loader import is_evaluation_enabled
        evaluation_enabled: bool = is_evaluation_enabled()
    except ImportError:
        import os
        evaluation_enabled = bool(os.environ.get("OPENAI_API_KEY", ""))

    if not evaluation_enabled:
        logger.info(
            "[eval] OPENAI_API_KEY not configured - evaluation skipped for all combos."
        )
        for combo in combos:
            if combo.run_dir and combo.run_dir.exists():
                _ensure_metrics_and_summary(combo.run_dir)
        return {}

    results: dict[str, dict[str, Any]] = {}

    for combo in combos:
        if not combo.run_dir or not combo.run_dir.exists():
            logger.warning(
                "[eval] No run_dir for combo '%s', skipping evaluation.",
                combo.alias,
            )
            continue

        logger.info("[eval] Evaluating combo '%s' - run_dir=%s", combo.alias, combo.run_dir)
        try:
            from src.evaluation.run_evaluation import evaluate_run
            counts: dict[str, Any] = evaluate_run(
                run_dir=combo.run_dir, pending_only=True
            )
            results[combo.alias] = counts or {}
        except (ImportError, ValueError, RuntimeError, OSError) as exc:
            tb_str = traceback.format_exc()
            err_report = _format_error_report(
                f"evaluate_run for combo={combo.alias}",
                exc,
                tb_str,
            )
            logger.error("%s", err_report)
            results[combo.alias] = {"error": str(exc)}
        finally:

            _ensure_metrics_and_summary(combo.run_dir)

    return results


COMPARISON_METRICS: list[tuple[str, str]] = [
    ("correctness_mean",          "\\abbr{Correct}{Correct.\\textsuperscript{c}}"),
    ("faithfulness_mean",         "\\abbr{Faith}{Faith.\\textsuperscript{c}}"),
    ("answer_relevance_mean",     "\\abbr{AnsRel}{AnsRel.\\textsuperscript{c}}"),
    ("overall_mean",              "\\abbr{Global}{Global\\textsuperscript{c}}"),
    ("latency_mean_ms",           "\\abbr{Lat}{Lat. (ms)}"),
]

TABLE_METRICS: list[tuple[str, str]] = [
    ("correctness_mean",          "\\abbr{Correct}{Correct.\\textsuperscript{c}}"),
    ("faithfulness_mean",         "\\abbr{Faith}{Faith.\\textsuperscript{c}}"),
    ("answer_relevance_mean",     "\\abbr{AnsRel}{AnsRel.\\textsuperscript{c}}"),
    ("overall_mean",              "\\abbr{Global}{Global\\textsuperscript{c}}"),
    ("answer_accuracy",           "\\abbr{Acc}{Acc. \\%}"),
    ("context_sufficiency_rate",  "\\abbr{CtxSuf}{Ctx.\\,Suf. \\%}"),
    ("generation_failure_rate",   "\\abbr{GenFail}{GenFail. \\%}"),
    ("retrieval_failure_rate",    "\\abbr{RetFail}{RetFail. \\%}"),
    ("latency_mean_ms",           "\\abbr{Lat}{Lat. (ms)}"),
]


def _load_combo_summary(combo: ComboSpec) -> dict[str, Any] | None:

    if not combo.run_dir:
        return None

    summary_path: Path = combo.run_dir / "summaries" / "experiment_summary.json"
    if not summary_path.exists():
        logger.warning(
            "No summary found for combo '%s' at %s", combo.alias, summary_path
        )
        return None

    try:
        with open(summary_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(
            "Cannot load summary for combo '%s': %s - %s",
            combo.alias, type(exc).__name__, exc,
        )
        return None


def _extract_metrics_from_summary(
    summary: dict[str, Any],
) -> dict[str, dict[str, float]]:

    metrics: dict[str, dict[str, float]] = {}
    experiments: dict[str, Any] = summary.get("experiments", {})

    for config_name, exp_data in experiments.items():

        status: str = exp_data.get("status", "")
        if status not in ("completed", "partial"):
            continue

        exp_metrics: dict[str, float] = {}


        sources: list[dict[str, Any]] = [
            exp_data.get("performance_metrics") or {},
            exp_data.get("quality_metrics") or {},
            exp_data.get("evaluation") or {},
        ]

        for src in sources:
            for key, value in src.items():
                if isinstance(value, (int, float)):
                    exp_metrics[key] = float(value)


        perf_src: dict[str, Any] = exp_data.get("performance_metrics") or {}
        if perf_src:
            for key in ("latency_mean_ms", "tokens_prompt_mean", "tokens_generated_mean"):
                if key in perf_src:
                    exp_metrics[key] = float(perf_src[key])
        else:

            for m in exp_data.get("metrics", []):
                key = m.get("metric")
                value = m.get("value")
                if key and isinstance(value, (int, float)):
                    exp_metrics[str(key)] = float(value)

        if exp_metrics:
            metrics[config_name] = exp_metrics

    return metrics


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _quality_score(metrics: dict[str, float]) -> float:
    return sum(
        metrics.get(metric_key, 0.0) * weight
        for metric_key, weight in QUALITY_WEIGHTS.items()
    )


def _combo_alias_from_summary(summary: dict[str, Any], known_combos: list[ComboSpec]) -> str:
    explicit = str(summary.get("combo_alias", "") or "").strip()
    if explicit:
        return explicit

    model_label = str(summary.get("model_label", "") or "").strip()
    for combo in known_combos:
        if model_label.endswith(f"__{combo.alias}"):
            return combo.alias

    source_file = str(summary.get("_source_file", "") or "")
    for combo in known_combos:
        if combo.alias in source_file:
            return combo.alias

    return "unknown"


def _is_combo_sweep_summary(summary: dict[str, Any], known_combos: list[ComboSpec]) -> bool:
    family = str(summary.get("experiment_family", "") or "").strip()
    if family == EXPERIMENT_FAMILY:
        return True

    model_label = str(summary.get("model_label", "") or "")
    return any(model_label.endswith(f"__{combo.alias}") for combo in known_combos)


def _load_summary_with_metadata(
    summary_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if summary.get("schema_version") != "2.0":
        return None
    if summary.get("report_type") != "experiment_summary":
        return None

    summary["_source_file"] = str(summary_path)

    run_dir = summary_path.parent.parent
    metadata: dict[str, Any] = {}

    metadata_path = run_dir / "artifact_metadata.json"
    if metadata_path.exists():
        try:
            metadata.update(json.loads(metadata_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass

    for key, value in metadata.items():
        summary.setdefault(key, value)

    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for key, value in manifest.items():
                summary.setdefault(key, value)
                metadata.setdefault(key, value)
        except (OSError, json.JSONDecodeError):
            pass

    return summary, metadata


def _discover_combo_summaries(
    combos: list[ComboSpec],
    log_dir: Path,
) -> list[dict[str, Any]]:

    runs_dir = log_dir / "runs"
    if not runs_dir.exists():
        return []

    summaries: list[dict[str, Any]] = []
    seen_run_ids: set[str] = set()

    for summary_path in sorted(runs_dir.glob("*/summaries/experiment_summary.json")):
        loaded = _load_summary_with_metadata(summary_path)
        if loaded is None:
            continue

        summary, metadata = loaded


        if not _is_combo_sweep_summary(summary, combos):
            continue


        combo_alias = _combo_alias_from_summary(summary, combos)
        if combo_alias == "unknown":
            continue

        run_id = str(summary.get("run_id", "") or summary_path.parent.parent.name)
        if run_id in seen_run_ids:
            continue
        seen_run_ids.add(run_id)

        summary["combo_alias"] = combo_alias
        summaries.append(summary)

    return summaries


def _combo_records_from_summaries(
    summaries: list[dict[str, Any]],
    combos: list[ComboSpec],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for summary in summaries:
        combo_alias = _combo_alias_from_summary(summary, combos)
        if combo_alias == "unknown":
            continue

        dataset = str(summary.get("dataset", "") or "unknown")
        llm = _summary_llm_label(summary, combo_alias)
        metrics_by_config = _extract_metrics_from_summary(summary)

        for config_name, metrics in metrics_by_config.items():
            row: dict[str, Any] = {
                "dataset": dataset,
                "llm": llm,
                "combo": combo_alias,
                "config": config_name,
                "is_combo_selection_config": config_name in COMBO_SELECTION_CONFIGS,
                "quality_score": _quality_score(metrics),
            }

            for metric_key, _ in TABLE_METRICS:
                row[metric_key] = float(metrics.get(metric_key, 0.0))

            records.append(row)

    return records


def _write_records_csv(records: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        out.write_text("", encoding="utf-8")
        return out

    fieldnames: list[str] = [
        "dataset",
        "llm",
        "combo",
        "config",
        "is_combo_selection_config",
        "quality_score",
    ] + [metric_key for metric_key, _ in TABLE_METRICS]

    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    return out


def _write_dict_rows_csv(rows: list[dict[str, Any]], out: Path) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        out.write_text("", encoding="utf-8")
        return out

    fieldnames: list[str] = []
    seen: set[str] = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    return out


def _assign_ranks(
    rows: list[dict[str, Any]],
    group_keys: list[str],
) -> None:

    current_group: tuple[str, ...] | None = None
    rank = 0

    for row in rows:
        group = tuple(str(row.get(k, "")) for k in group_keys)
        if group != current_group:
            current_group = group
            rank = 1
        else:
            rank += 1
        row["rank"] = rank


def _aggregate_combo_records_by_llm(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    filtered = [r for r in records if r.get("is_combo_selection_config")]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for row in filtered:
        key = (
            str(row["dataset"]),
            str(row["llm"]),
            str(row["combo"]),
        )
        groups.setdefault(key, []).append(row)

    aggregated: list[dict[str, Any]] = []

    for (dataset, llm, combo), rows in groups.items():
        score_values = [float(r.get("quality_score", 0.0)) for r in rows]
        overall_values = [float(r.get("overall_mean", 0.0)) for r in rows]
        faith_values = [float(r.get("faithfulness_mean", 0.0)) for r in rows]
        correct_values = [float(r.get("correctness_mean", 0.0)) for r in rows]
        relevance_values = [float(r.get("answer_relevance_mean", 0.0)) for r in rows]
        latency_values = [float(r.get("latency_mean_ms", 0.0)) for r in rows]
        config_names = sorted({str(r.get("config", "")) for r in rows})

        aggregated.append({
            "dataset": dataset,
            "llm": llm,
            "combo": combo,
            "quality_score": _mean(score_values),
            "overall_mean": _mean(overall_values),
            "faithfulness_mean": _mean(faith_values),
            "correctness_mean": _mean(correct_values),
            "answer_relevance_mean": _mean(relevance_values),
            "latency_mean_ms": _mean(latency_values),
            "std_across_configs": _std(score_values),
            "std_across_llms": 0.0,
            "num_llms": 1,
            "num_configs": len(config_names),
            "num_config_rows": len(rows),
        })

    aggregated.sort(
        key=lambda r: (
            str(r["dataset"]),
            str(r["llm"]),
            -float(r["quality_score"]),
            float(r["std_across_configs"]),
            float(r["latency_mean_ms"]),
        )
    )
    _assign_ranks(aggregated, group_keys=["dataset", "llm"])

    return aggregated


def _aggregate_combo_records_across_llms(
    per_llm_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for row in per_llm_rows:
        key = (
            str(row["dataset"]),
            str(row["combo"]),
        )
        groups.setdefault(key, []).append(row)

    aggregated: list[dict[str, Any]] = []

    for (dataset, combo), rows in groups.items():
        score_values = [float(r.get("quality_score", 0.0)) for r in rows]
        overall_values = [float(r.get("overall_mean", 0.0)) for r in rows]
        faith_values = [float(r.get("faithfulness_mean", 0.0)) for r in rows]
        correct_values = [float(r.get("correctness_mean", 0.0)) for r in rows]
        relevance_values = [float(r.get("answer_relevance_mean", 0.0)) for r in rows]
        latency_values = [float(r.get("latency_mean_ms", 0.0)) for r in rows]
        config_std_values = [float(r.get("std_across_configs", 0.0)) for r in rows]
        llms = sorted({str(r.get("llm", "")) for r in rows})

        aggregated.append({
            "dataset": dataset,
            "llm": "aggregate_all_llms",
            "combo": combo,
            "quality_score": _mean(score_values),
            "overall_mean": _mean(overall_values),
            "faithfulness_mean": _mean(faith_values),
            "correctness_mean": _mean(correct_values),
            "answer_relevance_mean": _mean(relevance_values),
            "latency_mean_ms": _mean(latency_values),
            "std_across_configs": _mean(config_std_values),
            "std_across_llms": _std(score_values),
            "num_llms": len(llms),
            "num_configs": int(round(_mean([
                float(r.get("num_configs", 0.0)) for r in rows
            ]))),
            "num_config_rows": int(sum(
                int(r.get("num_config_rows", 0)) for r in rows
            )),
        })

    aggregated.sort(
        key=lambda r: (
            str(r["dataset"]),
            -float(r["quality_score"]),
            float(r["std_across_llms"]),
            float(r["std_across_configs"]),
            float(r["latency_mean_ms"]),
        )
    )
    _assign_ranks(aggregated, group_keys=["dataset"])

    return aggregated


def _safe_column_label(text: Any) -> str:

    s = "".join(
        ch.lower() if ch.isalnum() else "_"
        for ch in str(text or "unknown")
    )
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "unknown"


def _llm_column_prefixes(llms: list[str]) -> dict[str, str]:

    prefixes: dict[str, str] = {}
    counts: dict[str, int] = {}

    for llm in llms:
        base = _safe_column_label(llm)
        counts[base] = counts.get(base, 0) + 1

        if counts[base] == 1:
            prefixes[llm] = base
        else:
            prefixes[llm] = f"{base}_{counts[base]}"

    return prefixes


def _build_combo_score_matrix_rows(
    by_llm_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], dict[str, str]]:

    llms: list[str] = sorted({
        str(row.get("llm", ""))
        for row in by_llm_rows
        if str(row.get("llm", "")).strip()
    })
    llm_prefixes: dict[str, str] = _llm_column_prefixes(llms)

    aggregate_by_key: dict[tuple[str, str], dict[str, Any]] = {
        (str(row.get("dataset", "")), str(row.get("combo", ""))): row
        for row in aggregate_rows
    }

    per_key_rows: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in by_llm_rows:
        key = (
            str(row.get("dataset", "")),
            str(row.get("combo", "")),
        )
        per_key_rows.setdefault(key, []).append(row)

    all_keys: set[tuple[str, str]] = set(aggregate_by_key.keys()) | set(per_key_rows.keys())

    matrix_rows: list[dict[str, Any]] = []

    for dataset, combo in sorted(all_keys):
        aggregate = aggregate_by_key.get((dataset, combo), {})
        rows_for_combo = per_key_rows.get((dataset, combo), [])
        row_by_llm: dict[str, dict[str, Any]] = {
            str(r.get("llm", "")): r
            for r in rows_for_combo
        }

        matrix_row: dict[str, Any] = {
            "dataset": dataset,
            "combo": combo,
            "aggregate_rank": int(aggregate.get("rank", 0) or 0),
            "aggregate_score": float(aggregate.get("quality_score", 0.0) or 0.0),
            "aggregate_overall": float(aggregate.get("overall_mean", 0.0) or 0.0),
            "aggregate_faithfulness": float(aggregate.get("faithfulness_mean", 0.0) or 0.0),
            "aggregate_correctness": float(aggregate.get("correctness_mean", 0.0) or 0.0),
            "aggregate_relevance": float(aggregate.get("answer_relevance_mean", 0.0) or 0.0),
            "aggregate_latency_ms": float(aggregate.get("latency_mean_ms", 0.0) or 0.0),
            "aggregate_std_across_llms": float(aggregate.get("std_across_llms", 0.0) or 0.0),
            "aggregate_std_across_configs": float(aggregate.get("std_across_configs", 0.0) or 0.0),
            "num_llms": int(aggregate.get("num_llms", 0) or 0),
            "num_configs": int(aggregate.get("num_configs", 0) or 0),
        }

        for llm in llms:
            prefix = llm_prefixes[llm]
            llm_row = row_by_llm.get(llm)

            if llm_row is None:
                matrix_row[f"{prefix}_rank"] = ""
                matrix_row[f"{prefix}_score"] = ""
                matrix_row[f"{prefix}_overall"] = ""
                matrix_row[f"{prefix}_faithfulness"] = ""
                matrix_row[f"{prefix}_correctness"] = ""
                matrix_row[f"{prefix}_relevance"] = ""
                matrix_row[f"{prefix}_latency_ms"] = ""
                matrix_row[f"{prefix}_std_across_configs"] = ""
                continue

            matrix_row[f"{prefix}_rank"] = int(llm_row.get("rank", 0) or 0)
            matrix_row[f"{prefix}_score"] = float(llm_row.get("quality_score", 0.0) or 0.0)
            matrix_row[f"{prefix}_overall"] = float(llm_row.get("overall_mean", 0.0) or 0.0)
            matrix_row[f"{prefix}_faithfulness"] = float(llm_row.get("faithfulness_mean", 0.0) or 0.0)
            matrix_row[f"{prefix}_correctness"] = float(llm_row.get("correctness_mean", 0.0) or 0.0)
            matrix_row[f"{prefix}_relevance"] = float(llm_row.get("answer_relevance_mean", 0.0) or 0.0)
            matrix_row[f"{prefix}_latency_ms"] = float(llm_row.get("latency_mean_ms", 0.0) or 0.0)
            matrix_row[f"{prefix}_std_across_configs"] = float(llm_row.get("std_across_configs", 0.0) or 0.0)

        matrix_rows.append(matrix_row)

    matrix_rows.sort(
        key=lambda r: (
            str(r.get("dataset", "")),
            int(r.get("aggregate_rank", 0) or 999999),
            -float(r.get("aggregate_score", 0.0) or 0.0),
            str(r.get("combo", "")),
        )
    )

    return matrix_rows, llms, llm_prefixes


def _write_combo_score_matrix_table(
    rows: list[dict[str, Any]],
    llms: list[str],
    llm_prefixes: dict[str, str],
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        out.write_text(
            "% No data available for combo score matrix\n",
            encoding="utf-8",
        )
        return out

    col_format = "llrrr" + "l" * len(llms)

    header_cells: list[str] = [
        "Dataset",
        "Combo",
        "\\abbr{AggRank}{Agg.\\,Rank}",
        "\\abbr{AggScore}{Agg.\\,Score}",
        "\\abbr{StdLLM}{Std.\\,\\acro{LLM}}",
    ] + [
        f"{_latex_escape(llm)} Score/Rank"
        for llm in llms
    ]

    header = " & ".join(header_cells)

    lines: list[str] = [

        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{0.88}",
        f"\\begin{{longtable}}{{{col_format}}}",
        (
            "  \\caption{Matriz comparativa de combinaciones retriever "
            "$\\times$ reranker por \\acro{LLM}. \\\\ Cada celda muestra "
            "puntuación ponderada/ranking dentro del \\acro{LLM}.}\\\\"
        ),
        "  \\label{tab:combo_score_matrix_by_llm}\\\\",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endfirsthead",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endhead",
    ]

    for row in rows:
        cells: list[str] = [
            _latex_escape(row.get("dataset", "")),
            _latex_escape(row.get("combo", "")),
            str(int(row.get("aggregate_rank", 0) or 0)),
            f"{_dfmt(float(row.get('aggregate_score', 0.0) or 0.0), 2)}",
            f"{_dfmt(float(row.get('aggregate_std_across_llms', 0.0) or 0.0), 2)}",
        ]

        for llm in llms:
            prefix = llm_prefixes[llm]
            score = row.get(f"{prefix}_score", "")
            rank = row.get(f"{prefix}_rank", "")

            if score in ("", None) or rank in ("", None):
                cells.append("--")
            else:
                cells.append(f"{_dfmt(float(score), 2)} / {int(rank)}")

        lines.append("  " + " & ".join(cells) + " \\")

    lines += [
        "  \\bottomrule",
        "\\end{longtable}",
        "\\normalsize",

    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _write_combo_ranking_table(
    rows: list[dict[str, Any]],
    out: Path,
    caption: str,
    label: str,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "\\begin{table}[H]",
        "  \\centering",
        "  \\scriptsize",
        "  \\setlength{\\tabcolsep}{3pt}",
        "  \\renewcommand{\\arraystretch}{0.92}",
        "  \\resizebox{\\textwidth}{!}{%",
        "  \\begin{tabular}{rllrrrrrrrrrr}",
        "    \\toprule",
        (
            "    Rank & \\acro{LLM} & Combo & \\acro{LLM}s & Cfgs & Puntuación & "
            "\\abbr{Global}{Global\\textsuperscript{c}} & "
            "\\abbr{Faith}{Faith.\\textsuperscript{c}} & "
            "\\abbr{Correct}{Correct.\\textsuperscript{c}} & "
            "\\abbr{AnsRel}{AnsRel.\\textsuperscript{c}} & "
            "\\abbr{Lat}{Lat. (ms)} & \\abbr{StdCfg}{Std.\\,Cfg} & "
            "\\abbr{StdLLM}{Std.\\,\\acro{LLM}} \\\\"
        ),
        "    \\midrule",
    ]

    for row in rows:
        lines.append(
            "    "
            f"{int(row.get('rank', 0))} & "
            f"{_latex_escape(row.get('llm', ''))} & "
            f"{_latex_escape(row.get('combo', ''))} & "
            f"{int(row.get('num_llms', 1))} & "
            f"{int(row.get('num_configs', 0))} & "
            f"{_dfmt(float(row.get('quality_score', 0.0)), 2)} & "
            f"{_dfmt(float(row.get('overall_mean', 0.0)), 2)} & "
            f"{_dfmt(float(row.get('faithfulness_mean', 0.0)), 2)} & "
            f"{_dfmt(float(row.get('correctness_mean', 0.0)), 2)} & "
            f"{_dfmt(float(row.get('answer_relevance_mean', 0.0)), 2)} & "
            f"{float(row.get('latency_mean_ms', 0.0)):.0f} & "
            f"{_dfmt(float(row.get('std_across_configs', 0.0)), 2)} & "
            f"{_dfmt(float(row.get('std_across_llms', 0.0)), 2)} \\\\"
        )

    lines += [
        "    \\bottomrule",
        "  \\end{tabular}%",
        "  }",
        f"  \\caption{{{caption}}}",
        f"  \\label{{{label}}}",
        "\\end{table}",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _write_full_combo_longtable(records: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        ("llm", "\\acro{LLM}"),
        ("combo", "Combo"),
        ("config", "Configuración"),
        ("quality_score", "Puntuación"),
        ("correctness_mean", "\\abbr{Correct}{Correct.\\textsuperscript{c}}"),
        ("faithfulness_mean", "\\abbr{Faith}{Faith.\\textsuperscript{c}}"),
        ("answer_relevance_mean", "\\abbr{AnsRel}{AnsRel.\\textsuperscript{c}}"),
        ("overall_mean", "\\abbr{Global}{Global\\textsuperscript{c}}"),
        ("latency_mean_ms", "\\abbr{Lat}{Lat. (ms)}"),
    ]

    col_format = "lll" + "r" * (len(columns) - 3)
    header = " & ".join(label for _, label in columns)

    lines = [

        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{0.88}",
        f"\\begin{{longtable}}{{{col_format}}}",
        "  \\caption{Resultados completos del barrido retriever x reranker}\\\\",
        "  \\label{tab:combo_sweep_full_results}\\\\",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endfirsthead",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endhead",
    ]

    for row in sorted(records, key=lambda r: (str(r["llm"]), str(r["combo"]), str(r["config"]))):
        vals: list[str] = []
        for key, _ in columns:
            value = row.get(key, "")
            if key in {"llm", "combo", "config"}:
                vals.append(_latex_escape(value))
            elif key == "latency_mean_ms":
                vals.append(f"{float(value):.0f}")
            else:
                vals.append(f"{_dfmt(float(value), 2)}")
        lines.append("  " + " & ".join(vals) + " \\\\")

    lines += [
        "  \\bottomrule",
        "\\end{longtable}",
        "\\normalsize",

    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _write_combo_ranking_chart(rows: list[dict[str, Any]], out: Path) -> Path:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np
    except ImportError as exc:
        logger.error("matplotlib not available: %s", exc)
        return out

    out.parent.mkdir(parents=True, exist_ok=True)

    ordered = list(reversed(rows))
    labels = [str(r["combo"]) for r in ordered]
    values = [float(r["quality_score"]) for r in ordered]
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9, max(4, len(labels) * 0.55)))
    bars = ax.barh(y, values)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{_dfmt(value, 2)}",
            va="center",
            ha="left",
            fontsize=9,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Puntuación de calidad ponderada (0-100 pts)", fontsize=11)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_es_yformatter))
    ax.set_title("Ranking de combinaciones retriever × reranker")
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return out


def _write_combo_selection_bundle(
    records: list[dict[str, Any]],
    output_dir: Path,
    llm_label: str,
    diagnostics: bool = True,
) -> list[Path]:
    datasets = sorted({str(r["dataset"]) for r in records})
    dataset_label = datasets[0] if len(datasets) == 1 else "mixed_datasets"

    root = (
        output_dir
        / "combo_sweep"
        / _safe_path_label(dataset_label)
        / _safe_path_label(llm_label)
    )

    thesis_dir = root / "thesis_compact"
    appendix_dir = root / "appendix"
    diagnostics_dir = root / "diagnostics"
    raw_dir = root / "raw_evidence"

    generated: list[Path] = []

    raw_csv = raw_dir / "combo_by_config_all_metrics.csv"
    generated.append(_write_records_csv(records, raw_csv))

    raw_json = raw_dir / "combo_by_config_all_metrics.json"
    raw_json.parent.mkdir(parents=True, exist_ok=True)
    raw_json.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(raw_json)

    by_llm_rows = _aggregate_combo_records_by_llm(records)
    llm_diagnostic_rows = _aggregate_llm_diagnostic_rows(by_llm_rows)

    llms_in_records = sorted({str(r["llm"]) for r in records})
    if len(llms_in_records) == 1:
        aggregate_rows = [dict(r) for r in by_llm_rows]
    else:
        aggregate_rows = _aggregate_combo_records_across_llms(by_llm_rows)

    matrix_rows, matrix_llms, matrix_prefixes = _build_combo_score_matrix_rows(
        by_llm_rows=by_llm_rows,
        aggregate_rows=aggregate_rows,
    )

    generated.append(_write_dict_rows_csv(
        aggregate_rows,
        raw_dir / "combo_ranking_aggregate.csv",
    ))

    generated.append(_write_dict_rows_csv(
        llm_diagnostic_rows,
        raw_dir / "llm_diagnostic_summary.csv",
    ))

    generated.append(_write_dict_rows_csv(
        by_llm_rows,
        raw_dir / "combo_ranking_by_llm.csv",
    ))

    generated.append(_write_dict_rows_csv(
        matrix_rows,
        raw_dir / "combo_score_matrix_by_llm.csv",
    ))

    generated.append(_write_combo_ranking_table(
        aggregate_rows,
        thesis_dir / "combo_ranking_aggregate.tex",
        caption="Ranking de combinaciones retriever x reranker",
        label=f"tab:combo_ranking_{_safe_path_label(llm_label)}",
    ))

    generated.append(_write_combo_ranking_table(
        by_llm_rows,
        thesis_dir / "combo_ranking_by_llm.tex",
        caption="Ranking de combinaciones retriever x reranker por \\acro{LLM}",
        label=f"tab:combo_ranking_by_llm_{_safe_path_label(llm_label)}",
    ))

    generated.append(_write_combo_score_matrix_table(
        matrix_rows,
        matrix_llms,
        matrix_prefixes,
        thesis_dir / "combo_score_matrix_by_llm.tex",
    ))

    generated.append(_write_combo_ranking_chart(
        aggregate_rows,
        thesis_dir / "combo_quality_score_ranking.png",
    ))

    generated.append(_write_full_combo_longtable(
        records,
        appendix_dir / "combo_by_config_full_longtable.tex",
    ))

    if diagnostics:
        generated.append(_write_dict_rows_csv(
            by_llm_rows,
            diagnostics_dir / "combo_ranking_by_llm_diagnostic.csv",
        ))

    logger.info("Generated combo-selection artifact bundle under %s", root)
    return generated


def generate_combo_selection_artifacts(
    combos: list[ComboSpec],
    output_dir: Path,
    summaries: list[dict[str, Any]],
    diagnostics: bool = True,
) -> list[Path]:
    records = _combo_records_from_summaries(summaries, combos)
    if not records:
        logger.warning("No combo-sweep records found. No combo artifacts generated.")
        return []

    llms = sorted({str(r["llm"]) for r in records})

    generated: list[Path] = []

    aggregate_label = llms[0] if len(llms) == 1 else "aggregate_all_llms"
    generated.extend(_write_combo_selection_bundle(
        records=records,
        output_dir=output_dir,
        llm_label=aggregate_label,
        diagnostics=diagnostics,
    ))

    if len(llms) > 1:
        for llm in llms:
            llm_records = [r for r in records if str(r["llm"]) == llm]
            generated.extend(_write_combo_selection_bundle(
                records=llm_records,
                output_dir=output_dir,
                llm_label=llm,
                diagnostics=diagnostics,
            ))


    datasets = sorted({str(r["dataset"]) for r in records})
    dataset_label = datasets[0] if len(datasets) == 1 else "mixed_datasets"
    aggregate_base_dir: Path = (
        output_dir
        / "combo_sweep"
        / _safe_path_label(dataset_label)
        / _safe_path_label(aggregate_label)
    )
    generate_compact_combo_thesis_artifacts(aggregate_base_dir)

    return generated


def _discover_combo_run_dirs(
    combos: list[ComboSpec],
    log_dir: Path,
) -> None:

    runs_dir: Path = log_dir / "runs"
    if not runs_dir.exists():
        logger.warning("_discover_combo_run_dirs: %s does not exist.", runs_dir)
        return


    alias_to_dirs: dict[str, list[Path]] = {}
    for run_dir in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not run_dir.is_dir():
            continue
        manifest_path: Path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            continue
        try:
            with open(manifest_path, encoding="utf-8") as fh:
                manifest: dict[str, Any] = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        label: str = manifest.get("model_label", "")
        if not label:
            continue
        alias_to_dirs.setdefault(label, []).append(run_dir)

    matched = 0
    for combo in combos:
        if combo.run_dir:
            continue
        candidates: list[Path] = alias_to_dirs.get(combo.alias, [])

        if not candidates:
            for label, dirs in alias_to_dirs.items():
                if label.endswith(f"__{combo.alias}"):
                    candidates.extend(dirs)
        if candidates:
            combo.run_dir = candidates[0]
            logger.info(
                "_discover_combo_run_dirs: combo '%s' → %s",
                combo.alias, combo.run_dir.name,
            )
            matched += 1
        else:
            logger.warning(
                "_discover_combo_run_dirs: no run dir found for combo '%s'.",
                combo.alias,
            )

    logger.info(
        "_discover_combo_run_dirs: matched %d / %d combos.", matched, len(combos)
    )


def generate_combo_charts(
    combo: ComboSpec,
    output_dir: Path,
) -> list[Path]:

    summary: dict[str, Any] | None = _load_combo_summary(combo)
    if summary is None:
        logger.warning(
            "Skipping chart generation for combo '%s' - no summary.", combo.alias
        )
        return []

    metrics: dict[str, dict[str, float]] = _extract_metrics_from_summary(summary)
    if not metrics:
        logger.warning(
            "Skipping chart generation for combo '%s' - no metrics.", combo.alias
        )
        return []

    from scripts.generate_charts import (
        generate_quality_chart,
        generate_latency_chart,
        generate_latex_table,
        generate_improvement_chart,
    )

    combo_dir: Path = output_dir / combo.alias
    combo_dir.mkdir(parents=True, exist_ok=True)

    dataset: str = summary.get("dataset", "unknown")
    model: str = _summary_llm_label(summary, combo.alias)
    title: str = (
        f"Retriever: {COMBO_ALIASES.get(combo.retrieval_model, combo.retrieval_model)}"
        f"  ×  Reranker: {COMBO_ALIASES.get(combo.reranker_model, combo.reranker_model)}"
        f"\nDataset: {dataset}  |  Modelo LLM: {model}"
    )

    generated: list[Path] = []

    generated.append(
        generate_quality_chart(metrics, combo_dir, title_suffix=title)
    )
    generated.append(
        generate_latency_chart(metrics, combo_dir, title_suffix=title)
    )
    generated.append(
        generate_latex_table(
            metrics, combo_dir,
            dataset=f"{dataset}__{combo.alias}",
            model=model,
        )
    )
    generated.append(
        generate_improvement_chart(metrics, combo_dir, title_suffix=title)
    )

    return generated


@deprecated("Old chart")
def generate_cross_combo_quality_chart(
    combos: list[ComboSpec],
    output_dir: Path,
    pipeline_config: str = "optimized_k_rr",
) -> Path:

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np
    except ImportError as exc:
        logger.error(
            "matplotlib not available - %s: %s. Install: pip install matplotlib",
            type(exc).__name__, exc,
        )
        out: Path = output_dir / f"cross_combo_quality__{pipeline_config}.png"
        return out

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"cross_combo_quality__{pipeline_config}.png"

    dataset_label, llm_label = _cross_combo_metadata(combos)


    quality_cols: list[tuple[str, str]] = [
        (mk, label)
        for mk, label in COMPARISON_METRICS
        if mk != "latency_mean_ms"
    ]


    combo_labels: list[str] = []
    combo_values: list[list[float]] = []

    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue
        metrics = _extract_metrics_from_summary(summary)
        cfg_metrics: dict[str, float] = metrics.get(pipeline_config, {})
        if not cfg_metrics:
            logger.warning(
                "cross_combo_quality_chart: no data for config '%s' in combo '%s', skipping.",
                pipeline_config, combo.alias,
            )
            continue
        combo_labels.append(combo.alias)
        combo_values.append([cfg_metrics.get(mk, 0.0) for mk, _ in quality_cols])

    if not combo_labels:
        logger.warning(
            "cross_combo_quality_chart: no combo has data for config '%s'.",
            pipeline_config,
        )
        return out

    n_combos: int = len(combo_labels)
    n_metrics: int = len(quality_cols)
    x: Any = np.arange(n_metrics)
    width: float = min(0.7 / n_combos, 0.20)


    colors: list[str] = [
        plt.cm.tab10(i / max(n_combos, 1))
        for i in range(n_combos)
    ]

    fig, ax = plt.subplots(figsize=(max(10, n_metrics * 2.5), 6))

    for i, (alias, vals) in enumerate(zip(combo_labels, combo_values)):
        offset: float = (i - (n_combos - 1) / 2.0) * width
        bars = ax.bar(
            x + offset, vals, width,
            label=alias,
            color=colors[i],
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, val in zip(bars, vals):
            if val > 0.5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 0.8,
                    f"{_dfmt(val, 2)}",
                    ha="center", va="bottom",
                    fontsize=7, fontweight="bold",
                )

    ax.set_ylabel("Puntuación (0-100 pts)", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_es_yformatter))
    ax.set_title(
        f"Comparativa de Calidad entre Combinaciones Retriever × Reranker\n"
        f"Config: {pipeline_config} | Dataset: {dataset_label} | Modelo \\acro{{LLM}}: {llm_label}",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in quality_cols], fontsize=10)
    ax.set_ylim(0, 118)
    ax.legend(loc="upper right", fontsize=8, ncol=max(1, n_combos // 4))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("cross_combo_quality__%s.png → %s", pipeline_config, out)
    return out


@deprecated("Old table")
def generate_cross_combo_quality_table(
    combos: list[ComboSpec],
    output_dir: Path,
    primary_configs: list[str] | None = None,
) -> Path:

    if primary_configs is None:
        primary_configs = [

    "baseline_k",
    "baseline_s",
    "baseline_k_rr",
    "baseline_s_rr",

    "baseline_k_grounded",
    "baseline_s_grounded",
    "baseline_k_rr_grounded",
    "baseline_s_rr_grounded",

    "optimized_k",
    "optimized_s",
    "optimized_k_rr",
    "optimized_s_rr",

    "optimized_k_grounded",
    "optimized_s_grounded",
    "optimized_k_rr_grounded",
    "optimized_s_rr_grounded",
]


    quality_col_specs: list[tuple[str, str]] = COMPARISON_METRICS

    col_format: str = "ll" + "r" * len(quality_col_specs)
    header: str = "Combinación & Config & " + " & ".join(
        label for _, label in quality_col_specs
    )

    dataset_label, llm_label = _cross_combo_metadata(combos)

    caption: str = (
        "Comparación completa de calidad entre combinaciones "
        "retriever $\\times$ reranker"
    )
    if dataset_label or llm_label:
        caption += (
            f" en {_latex_escape(dataset_label or 'unknown')} "
            f"con modelo \\acro{{LLM}} {_latex_escape(llm_label or 'unknown')}"
        )

    lines: list[str] = [

        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{0.88}",
        f"\\begin{{longtable}}{{{col_format}}}",
        f"  \\caption{{{caption}}}\\\\",
        "  \\label{tab:cross_combo_quality}\\\\",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endfirsthead",
        "  \\toprule",
        f"  {header} \\\\",
        "  \\midrule",
        "  \\endhead",
    ]

    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue
        metrics = _extract_metrics_from_summary(summary)
        first_row: bool = True
        for cfg in primary_configs:
            cfg_metrics: dict[str, float] = metrics.get(cfg, {})
            if not cfg_metrics:
                continue
            alias_cell: str = _latex_escape(combo.alias) if first_row else ""
            cfg_cell: str = _latex_escape(cfg)
            first_row = False

            row_vals: list[str] = []
            for mk, _ in quality_col_specs:
                val: float = cfg_metrics.get(mk, 0.0)
                row_vals.append(
                    f"{val:.0f}" if "ms" in mk else f"{_dfmt(val, 2)}"
                )

            lines.append(
                f"  {alias_cell} & {cfg_cell} & "
                + " & ".join(row_vals)
                + " \\\\"
            )
        if not first_row:
            lines.append("    \\addlinespace[2pt]")

    lines += [
        "  \\bottomrule",
        "\\end{longtable}",
        "\\normalsize",

    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    out: Path = output_dir / "cross_combo_quality_table.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("cross_combo_quality_table.tex → %s", out)
    return out


@deprecated("Old table")
def generate_cross_combo_table(
    combos: list[ComboSpec],
    output_dir: Path,
    primary_configs: list[str] | None = None,
) -> Path:

    if primary_configs is None:
        primary_configs = [

    "baseline_k",
    "baseline_s",
    "baseline_k_rr",
    "baseline_s_rr",

    "baseline_k_grounded",
    "baseline_s_grounded",
    "baseline_k_rr_grounded",
    "baseline_s_rr_grounded",

    "optimized_k",
    "optimized_s",
    "optimized_k_rr",
    "optimized_s_rr",

    "optimized_k_grounded",
    "optimized_s_grounded",
    "optimized_k_rr_grounded",
    "optimized_s_rr_grounded",
]

    dataset_label, llm_label = _cross_combo_metadata(combos)


    col_specs: list[tuple[str, str, str]] = [
        (cfg, "faithfulness_mean",  f"{cfg}/Faith")
        for cfg in primary_configs
    ] + [
        (cfg, "latency_mean_ms",    f"{cfg}/Lat(ms)")
        for cfg in primary_configs
    ]

    rows: list[tuple[str, list[str]]] = []
    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue
        metrics = _extract_metrics_from_summary(summary)
        row_vals: list[str] = []
        for cfg, mk, _ in col_specs:
            val: float = metrics.get(cfg, {}).get(mk, 0.0)
            row_vals.append(
                f"{val:.0f}" if "ms" in mk else f"{_dfmt(val, 2)}"
            )
        rows.append((combo.alias, row_vals))

    if not rows:
        out: Path = output_dir / "cross_combo_table.tex"
        out.write_text(
            "% No data available for cross-combo comparison\n",
            encoding="utf-8",
        )
        return out

    col_format: str = "l" + "r" * len(col_specs)
    col_header: str = " & ".join(
        ["Combinación"] + [_latex_escape(label) for _, _, label in col_specs]
    )

    caption_text = f"Latencia total por combinación retriever $\\times$ reranker en {_latex_escape(dataset_label)} "\
                    f"con modelo \\acro{{LLM}} {_latex_escape(llm_label)}"

    table_label = "tab:combo_comparison"

    lines: list[str] = [
        "\\begin{table}[H]",
        "  \\centering",
        "  \\scriptsize",
        "  \\setlength{\\tabcolsep}{3pt}",
        "  \\renewcommand{\\arraystretch}{0.9}",
        "  \\resizebox{\\textwidth}{!}{%",
        f"  \\begin{{tabular}}{{{col_format}}}",
        "    \\toprule",
        f"    {col_header} \\\\",
        "    \\midrule",
    ]
    for alias, vals in rows:
        lines.append(
            f"    {_latex_escape(alias)} & " + " & ".join(vals) + " \\\\"
        )
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}%",
        "  }",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        "\\end{table}",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "cross_combo_table.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("cross_combo_table.tex → %s", out)
    return out


@deprecated("Old chart and table")
def generate_cross_combo_total_latency_artifacts(
    combos: list[ComboSpec],
    output_dir: Path,
    configs: list[str] | None = None,
) -> tuple[Path, Path]:

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np
    except ImportError as exc:
        logger.error(
            "matplotlib not available - %s: %s. Install: pip install matplotlib",
            type(exc).__name__, exc,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return (
            output_dir / "cross_combo_total_latency.png",
            output_dir / "cross_combo_total_latency_table.tex",
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    chart_path: Path = output_dir / "cross_combo_total_latency.png"
    table_path: Path = output_dir / "cross_combo_total_latency_table.tex"

    dataset_label, llm_label = _cross_combo_metadata(combos)

    rows: list[dict[str, Any]] = []

    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue

        metrics = _extract_metrics_from_summary(summary)
        if not metrics:
            continue


        cfg_names: list[str] = configs if configs is not None else list(metrics.keys())

        latencies: list[float] = []
        included_configs: list[str] = []

        for cfg in cfg_names:
            val = metrics.get(cfg, {}).get("latency_mean_ms")
            if val is None:
                continue
            latencies.append(float(val))
            included_configs.append(cfg)

        if not latencies:
            logger.warning(
                "cross_combo_total_latency: no latency data for combo '%s'",
                combo.alias,
            )
            continue

        total_latency_ms: float = sum(latencies)
        mean_latency_ms: float = total_latency_ms / len(latencies)

        rows.append({
            "combo": combo.alias,
            "total_latency_ms": total_latency_ms,
            "mean_latency_ms": mean_latency_ms,
            "num_configs": len(latencies),
            "configs": included_configs,
        })

    if not rows:
        logger.warning("cross_combo_total_latency: no data available.")
        table_path.write_text(
            "% No data available for cross-combo latency comparison\n",
            encoding="utf-8",
        )
        return chart_path, table_path


    rows.sort(key=lambda r: r["total_latency_ms"])


    labels: list[str] = [r["combo"] for r in rows]
    values_ms: list[float] = [r["total_latency_ms"] for r in rows]
    values_s: list[float] = [v / 1000.0 for v in values_ms]

    y: Any = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(11, max(4, len(labels) * 0.75)))
    bars = ax.barh(y, values_s, edgecolor="white", linewidth=0.5)

    for bar, val_s in zip(bars, values_s):
        ax.text(
            bar.get_width() + max(values_s) * 0.01,
            bar.get_y() + bar.get_height() / 2.0,
            f"{_dfmt(val_s, 2)}s",
            va="center",
            ha="left",
            fontsize=9,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Latencia total acumulada (s)", fontsize=11)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_es_yformatter))
    ax.set_title(
        "Latencia total por combinación Retriever × Reranker\n"
        f"Dataset: {dataset_label} | Modelo \\acro{{LLM}}: {llm_label}",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("cross_combo_total_latency.png → %s", chart_path)


    caption_text = f"Latencia total por combinación retriever $\\times$ reranker en {_latex_escape(dataset_label)} "\
                    f"con modelo \\acro{{LLM}} {_latex_escape(llm_label)}"

    table_label = "tab:cross_combo_total_latency"

    col_format: str = "lrrr"
    col_header: str = "Combinación & Configs & Total (ms) & Media (ms)"

    lines: list[str] = [
        "\\begin{table}[H]",
        "  \\centering",
        "  \\scriptsize",
        "  \\setlength{\\tabcolsep}{3pt}",
        "  \\renewcommand{\\arraystretch}{0.9}",
        "  \\resizebox{\\textwidth}{!}{%",
        f"  \\begin{{tabular}}{{{col_format}}}",
        "    \\toprule",
        f"    {col_header} \\\\",
        "    \\midrule",
    ]
    for r in rows:
        lines.append(
            f"    {_latex_escape(r['combo'])} & "
            f"{r['num_configs']} & "
            f"{r['total_latency_ms']:.0f} & "
            f"{r['mean_latency_ms']:.0f} \\\\"
        )

    lines += [
        "    \\bottomrule",
        "  \\end{tabular}%",
        "  }",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        "\\end{table}",
    ]

    table_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("cross_combo_total_latency_table.tex → %s", table_path)

    return chart_path, table_path


def _aggregate_llm_diagnostic_rows(
    by_llm_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for row in by_llm_rows:
        key = (
            str(row["dataset"]),
            str(row["llm"]),
        )
        groups.setdefault(key, []).append(row)

    diagnostic_rows: list[dict[str, Any]] = []

    for (dataset, llm), rows in groups.items():
        score_values = [float(r.get("quality_score", 0.0)) for r in rows]
        overall_values = [float(r.get("overall_mean", 0.0)) for r in rows]
        faith_values = [float(r.get("faithfulness_mean", 0.0)) for r in rows]
        correct_values = [float(r.get("correctness_mean", 0.0)) for r in rows]
        relevance_values = [float(r.get("answer_relevance_mean", 0.0)) for r in rows]
        latency_values = [float(r.get("latency_mean_ms", 0.0)) for r in rows]

        ranks = [int(r.get("rank", 0)) for r in rows if int(r.get("rank", 0)) > 0]
        top_rank_count = sum(1 for rank in ranks if rank == 1)
        bottom_rank_count = sum(1 for rank in ranks if rank == max(ranks)) if ranks else 0

        diagnostic_rows.append({
            "dataset": dataset,
            "llm": llm,
            "mean_quality_score": _mean(score_values),
            "mean_overall": _mean(overall_values),
            "mean_faithfulness": _mean(faith_values),
            "mean_correctness": _mean(correct_values),
            "mean_answer_relevance": _mean(relevance_values),
            "mean_latency_ms": _mean(latency_values),
            "std_across_combos": _std(score_values),
            "num_combos": len(rows),
            "top_rank_count": top_rank_count,
            "bottom_rank_count": bottom_rank_count,
        })

    diagnostic_rows.sort(
        key=lambda r: (
            str(r["dataset"]),
            -float(r["mean_quality_score"]),
            float(r["std_across_combos"]),
            float(r["mean_latency_ms"]),
        )
    )

    _assign_ranks(diagnostic_rows, group_keys=["dataset"])

    return diagnostic_rows


@deprecated("Old chart")
def generate_cross_combo_chart(
    combos: list[ComboSpec],
    output_dir: Path,
    primary_metric: str = "faithfulness_mean",
    primary_config: str = "optimized_k_rr",
) -> Path:

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        logger.error(
            "matplotlib not available - %s: %s. Install: pip install matplotlib",
            type(exc).__name__, exc,
        )
        out: Path = output_dir / "cross_combo_chart.png"
        return out

    labels: list[str] = []
    values: list[float] = []

    dataset_label, llm_label = _cross_combo_metadata(combos)

    for combo in combos:
        summary = _load_combo_summary(combo)
        if summary is None:
            continue
        metrics = _extract_metrics_from_summary(summary)
        val = metrics.get(primary_config, {}).get(primary_metric, None)
        if val is not None:
            labels.append(combo.alias)
            values.append(val)

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "cross_combo_chart.png"

    if not labels:
        logger.warning("No data for cross_combo_chart, skipping.")
        return out

    y: Any = np.arange(len(labels))
    colors: list[str] = [
        plt.cm.tab10(i / max(len(labels), 1)) for i in range(len(labels))
    ]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.9)))
    bars = ax.barh(y, values, color=colors, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height() / 2.0,
            f"{_dfmt(val, 2)}",
            va="center", ha="left", fontsize=9,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(primary_metric.replace("_", " ").title(), fontsize=11)
    ax.set_title(
        f"Comparación de combinaciones  - {primary_config} / {primary_metric}\n"
        f"Dataset: {dataset_label} | Modelo \\acro{{LLM}}: {llm_label}",
        fontsize=12,
        fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("cross_combo_chart.png → %s", out)
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Run retriever × reranker combination comparison for the RAG thesis"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full mini-batch comparison (default: 5 samples per config per combo):
  python3 scripts/run_retriever_comparison.py

  # Quick dry-run to validate orchestration:
  python3 scripts/run_retriever_comparison.py --dry-run

  # 10 samples per config:
  python3 scripts/run_retriever_comparison.py --max-samples 10

  # Only run specific pipeline configs:
  python3 scripts/run_retriever_comparison.py --configs 1 4 5 10 11

  # Skip evaluation, regenerate charts from existing logs:
  python3 scripts/run_retriever_comparison.py --skip-eval --generate-only

  # List combos and exit:
  python3 scripts/run_retriever_comparison.py --list-combos

WORKFLOW:
  1. Script runs ALL combinations sequentially (mini-batch per combo).
  2. After all combos finish, evaluates ALL runs together (sync mode).
  3. Generates per-combo charts + cross-combination LaTeX table and chart.
  4. If there are pending evaluations, shows the retry command.
  5. Always shows the chart generation command for the main experiments.

  Run this script TWICE for two LLM models (change model on the server
  between runs). Results from both runs accumulate in logs/.
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Use stub pipelines (no real LLM/torch). Validates orchestration.",
    )
    parser.add_argument(
        "--max-samples", type=int, default=DEFAULT_MAX_SAMPLES,
        help=f"Max samples per config per combo (default: {DEFAULT_MAX_SAMPLES})",
    )
    parser.add_argument(
        "--configs", nargs="+", type=int, default=DEFAULT_COMPARISON_CONFIGS,
        help=(
            "Pipeline config options to run in each combo. "
            f"Default: {DEFAULT_COMPARISON_CONFIGS}. "
            "1=no_rag, 2=baseline_k, 3=baseline_s, 4=baseline_k_rr, 5=baseline_s_rr, 6=baseline_k_grounded, "
            "7=baseline_s_grounded, 8=baseline_k_rr_grounded, 9=baseline_s_rr_grounded, 10=optimized_k, "
            "11=optimized_s, 12=optimized_k_rr, 13=optimized_s_rr, 14=optimized_k_grounded, "
            "15=optimized_s_grounded, 16=optimized_k_rr_grounded, 17=optimized_s_rr_grounded"
        ),
    )
    parser.add_argument(
        "--dataset", type=str, default=COMPARISON_DATASET,
        choices=["rag_domain", "hotpotqa", "triviaqa"],
        help=f"Dataset to use (default: {COMPARISON_DATASET})",
    )
    parser.add_argument(
        "--model-label", type=str, default="",
        help="LLM model label (e.g. 'llama3-8b'). Included in run IDs.",
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip Phase 2 evaluation (useful for re-generating charts only).",
    )
    parser.add_argument(
        "--generate-only", action="store_true",
        help=(
            "Skip ALL experiment execution. Only generate charts from existing "
            "combo run directories. Must be combined with --skip-eval or "
            "evaluation will fail since there are no fresh runs."
        ),
    )
    parser.add_argument(
        "--with-diagnostics",
        action="store_true",
        help=(
            "Also generate detailed per-combo diagnostic charts and tables. "
            "By default, only compact thesis artifacts, appendix tables, and raw evidence are generated."
        ),
    )
    parser.add_argument(
        "--aggregate-existing-combo-runs",
        action="store_true",
        default=False,
        help=(
            "When generating artifacts, scan all existing combo_sweep runs in logs/runs. "
            "Use this after running the sweep for multiple LLMs."
        ),
    )
    parser.add_argument(
        "--list-combos", action="store_true",
        help="Print the combination grid and exit.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=OUTPUT_DIR,
        help=f"Output directory for charts and tables (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--log-file", type=Path, default=None,
        help=(
            "Path to a file where the full run log (stdout + all loggers) is "
            "saved. If omitted, a timestamped file is created automatically "
            "under logs/cli_runs/. Use --log-file /dev/null to disable."
        ),
    )


    parser.add_argument(
        "--use-cache", action=argparse.BooleanOptionalAction, default=True,
        help="Enable staged artifact cache (default: on; use --no-use-cache to disable).",
    )
    parser.add_argument(
        "--refresh-cache", action="store_true",
        help="Ignore existing cache entries and overwrite them.",
    )
    parser.add_argument(
        "--cache-dir", type=Path,
        default=None,
        help=(
            "Cache root directory. "
            "Default: .cache/rag/<dataset> (automatic per-dataset isolation)."
        ),
    )
    parser.add_argument(
        "--cached-contexts", action=argparse.BooleanOptionalAction, default=True,
        help=(
            "Reuse cached final contexts per query. When hit, the pipeline "
            "skips query-embedding/retrieval/reranking and only does prompt "
            "+ LLM + eval. Default on; --no-cached-contexts disables it."
        ),
    )
    parser.add_argument(
        "--cached-only", action="store_true",
        help=(
            "Fail instead of recomputing missing cache stages. Use to "
            "verify that prepare_rag_artifacts.py covered everything."
        ),
    )
    parser.add_argument(
        "--prewarm-cache", action=argparse.BooleanOptionalAction, default=True,
        help=(
            "Pre-compute deterministic artifacts (ingestion, chunking, "
            "embeddings BGE, retrieval, reranking) for every combo BEFORE "
            "running the LLM. Analogous to model preloading. "
            "Default on; --no-prewarm-cache disables it."
        ),
    )
    return parser.parse_args(argv)


def _build_combo_grid() -> list[ComboSpec]:

    combos: list[ComboSpec] = []
    for retrieval_model in RETRIEVAL_MODELS:
        for reranker_model in RERANKER_MODELS:
            combos.append(ComboSpec(
                retrieval_model=retrieval_model,
                reranker_model=reranker_model,
            ))
    return combos


def _attach_file_logger(log_path: Path) -> None:

    if str(log_path) == "/dev/null":
        return

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler: logging.FileHandler = logging.FileHandler(
        log_path, mode="w", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )


    root_logger: logging.Logger = logging.getLogger()
    root_logger.addHandler(file_handler)


    root_logger.setLevel(logging.DEBUG)


def _prewarm_combos_before_experiments(
    cache_manager: Any,
    combos: list[ComboSpec],
    config_options: list[int],
    dataset: str,
    max_samples: int,
) -> None:

    from scripts.prepare_rag_artifacts import prepare_for_combo
    from scripts.run_experiments import DATASET_CORPUS_MAPPING as _DCM
    from src.cache import query_id_for as _qid
    from src.dataset_manager import DatasetManager
    from src.pipeline import RAGPipeline, PIPELINE_CONFIGS, CORPUS_DIR as _CORPUS_DIR

    ds_info: dict[str, Any] = _DCM.get(dataset, {})
    corpus_dir: Path = ds_info.get("corpus_dir", _CORPUS_DIR)
    corpus_prefixes: list[str] | None = ds_info.get("corpus_prefixes")

    logger.info("=" * 70)
    logger.info("PREWARM - cache deterministic artifacts before experiments")
    logger.info("  Combos: %d  |  Configs: %s", len(combos), config_options)
    logger.info("=" * 70)

    mgr: DatasetManager = DatasetManager()
    samples = mgr.load(dataset, max_samples=max_samples)
    questions: list[str] = [s.question for s in samples]
    query_ids: list[str] = [_qid(q) for q in questions]
    logger.info("Prewarm samples: %d", len(samples))

    for combo in combos:
        logger.info("--- Prewarm combo: %s ---", combo.alias)
        for opt in config_options:
            try:
                name: str = RAGPipeline.CONFIG_MAP[opt]
            except KeyError:
                continue
            cfg: dict[str, Any] = PIPELINE_CONFIGS[name]
            if cfg.get("chunker") == "none" or cfg.get("retriever") == "none":
                continue
            retrieval_model: str = (
                combo.retrieval_model if cfg.get("retriever") == "faiss" else "bm25"
            )
            reranker_value: str = cfg.get("reranker", "none")
            reranker_model: str | None = (
                combo.reranker_model if reranker_value not in (None, "none") else None
            )
            prepare_for_combo(
                config_option=opt,
                config_name=name,
                questions=questions,
                query_ids=query_ids,
                corpus_dir=corpus_dir,
                corpus_prefixes=corpus_prefixes,
                cache=cache_manager,
                retrieval_models=retrieval_model,
                reranker_models=reranker_model,
                top_k=int(cfg.get("top_k", 25)),
                reranker_top_n=int(cfg.get("reranker_top_n", cfg.get("top_k", 5))),
            )
    logger.info("PREWARM done - cache under %s", cache_manager.cache_dir)


def generate_compact_combo_thesis_artifacts(base_dir: Path) -> None:

    import pandas as pd

    raw_dir = base_dir / "raw_evidence"
    out_dir = base_dir / "thesis_compact"
    raw_metrics = raw_dir / "combo_by_config_all_metrics.csv"


    RAW_METRICS = raw_metrics

    RETRIEVER_LABELS = {
        "multi-qa-mini": "multi-qa-mini",
        "bge-base": "bge-base",
    }

    RERANKER_LABELS = {
        "ms-marco-L6": "ms-marco-L6",
        "ms-marco-L12": "ms-marco-L12",
        "bge-reranker": "bge-reranker",
    }

    LLM_ORDER = ["llama3.2:latest", "llama3:8b", "mistral:7b"]

    def is_true_series(series: pd.Series) -> pd.Series:
        return series.astype(str).str.lower().isin({"true", "1", "yes"})

    def split_combo(combo: str) -> tuple[str, str]:
        if "__" not in combo:
            raise ValueError(f"Invalid combo format: {combo}")
        retriever, reranker = combo.split("__", 1)
        return retriever, reranker

    def tex_model(text: str) -> str:
        return rf"\texttt{{{text}}}"

    def fmt_score(value: float) -> str:
        return f"{_dfmt(value, 2)}"

    def fmt_latency(value: float) -> str:
        if pd.isna(value):
            return "--"
        return f"{int(round(value))}"

    def load_selection_rows() -> pd.DataFrame:
        if not RAW_METRICS.exists():
            raise FileNotFoundError(
                f"Missing raw evidence file: {RAW_METRICS}\n"
                "Run scripts/run_retriever_comparison.py first."
            )

        df = pd.read_csv(RAW_METRICS)

        required = {
            "dataset",
            "llm",
            "combo",
            "config",
            "is_combo_selection_config",
            "quality_score",
            "latency_mean_ms",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in {RAW_METRICS}: {sorted(missing)}")

        sel = df[is_true_series(df["is_combo_selection_config"])].copy()

        if sel.empty:
            raise ValueError(
                "No combo-selection rows found. Expected rows with "
                "is_combo_selection_config=true."
            )

        return sel

    def compute_combo_ranking(sel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        by_combo_llm = (
            sel.groupby(["combo", "llm"], as_index=False)
            .agg(
                score=("quality_score", "mean"),
                latency_ms=("latency_mean_ms", "mean"),
                configs_per_llm=("config", "nunique"),
            )
        )


        by_combo_llm["rank_within_llm"] = (
            by_combo_llm.groupby("llm")["score"]
            .rank(method="min", ascending=False)
            .astype(int)
        )

        cfg_counts = (
            by_combo_llm.groupby("combo")["configs_per_llm"]
            .agg(lambda s: int(s.iloc[0]) if s.nunique() == 1 else f"{int(s.min())}-{int(s.max())}")
            .rename("configs_per_model")
        )

        ranking = (
            by_combo_llm.groupby("combo", as_index=False)
            .agg(
                score=("score", "mean"),
                latency_ms=("latency_ms", "mean"),
                n_llms=("llm", "nunique"),
                std_llm=("score", "std"),
            )
            .merge(cfg_counts, on="combo")
            .sort_values(["score", "latency_ms"], ascending=[False, True])
            .reset_index(drop=True)
        )

        ranking["rank"] = ranking.index + 1

        return ranking, by_combo_llm

    def decision_for_row(row: pd.Series) -> str:
        combo = row["combo"]
        rank = int(row["rank"])
        retriever, reranker = split_combo(combo)

        if rank == 1:
            return "Seleccionada."

        if retriever == "multi-qa-mini" and reranker == "ms-marco-L12":
            return "No seleccionada: menor calidad que L6."

        if retriever == "bge-base" and reranker == "bge-reranker":
            return rf"Mejor variante con {tex_model('bge-base')}, pero queda por debajo."

        if retriever == "multi-qa-mini" and reranker == "bge-reranker":
            return "No seleccionada: \\acro{BGE} no mejora MS MARCO."

        if retriever == "bge-base":
            return "No seleccionada."

        return "Descartada."

    def write_combo_ranking_table(ranking: pd.DataFrame) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "combo_ranking_decision_compact.tex"

        lines: list[str] = []
        lines.append(r"\begin{table}[H]")
        lines.append(r"\centering")
        lines.append(r"\scriptsize")
        lines.append(r"\setlength{\tabcolsep}{3pt}")
        lines.append(r"\begin{adjustbox}{max width=0.96\textwidth}")
        lines.append(r"\begin{tabular}{rllrrrl}")
        lines.append(r"\toprule")
        lines.append(
            r"\textbf{Rank} & "
            r"\textbf{Retriever} & "
            r"\textbf{Re-ranker} & "
            r"\textbf{Puntuación de calidad} & "
            r"\textbf{Latencia media (ms)} & "
            r"\textbf{Configs/modelo} & "
            r"\textbf{Decisión} \\"
        )
        lines.append(r"\midrule")

        for _, row in ranking.iterrows():
            retriever, reranker = split_combo(row["combo"])
            lines.append(
                f"{int(row['rank'])} & "
                f"{tex_model(RETRIEVER_LABELS.get(retriever, retriever))} & "
                f"{tex_model(RERANKER_LABELS.get(reranker, reranker))} & "
                f"{str(fmt_score(row['score'])).replace(".", ",")} & "
                f"{fmt_latency(row['latency_ms'])} & "
                f"{row['configs_per_model']} & "
                f"{decision_for_row(row)} \\\\"
            )

        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(r"\end{adjustbox}")
        lines.append(r"\caption{Resultado compacto del barrido retriever$\times$re-ranker sobre Trivia\acro{QA}.}")
        lines.append(r"\label{tab:combo_sweep_decision_triviaqa}")
        lines.append(r"\end{table}")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    def write_combo_selection_text(ranking: pd.DataFrame, by_combo_llm: pd.DataFrame) -> None:
        path = out_dir / "combo_selection_interpretation.tex"

        top = ranking.iloc[0]
        second = ranking.iloc[1]
        retriever, reranker = split_combo(top["combo"])
        gap = float(top["score"] - second["score"])

        top_by_llm = by_combo_llm[by_combo_llm["combo"] == top["combo"]]
        first_in_all_llms = bool((top_by_llm["rank_within_llm"] == 1).all())

        stability_sentence = (
            "Además, alcanza el primer puesto en los modelos generativos evaluados, "
            "lo que indica que la decisión no depende de un único \\acro{LLM}."
            if first_in_all_llms
            else
            "La matriz por modelo permite comprobar la estabilidad de esta decisión "
            "entre generadores."
        )

        text = (rf"""
    A partir de la Tabla~\ref{{tab:combo_sweep_decision_triviaqa}}, la combinación
    seleccionada para el cribado medio es
    \texttt{{sentence-transformers/multi-qa-MiniLM-L6-cos-v1}} como modelo de
    recuperación semántica y \texttt{{cross-encoder/ms-marco-MiniLM-L-6-v2}} como
    re-ranker. Esta combinación obtiene el mejor \emph{{puntuación de calidad ponderada}} del
    barrido agregado, con {str((fmt_score(top["score"]))).replace(".", ",")} puntos, y supera a la segunda
    alternativa por {str((fmt_score(gap))).replace(".", ",")} puntos. {stability_sentence} Frente a la
    alternativa \texttt{{cross-encoder/ms-marco-MiniLM-L-12-v2}}, la variante
    \texttt{{cross-encoder/ms-marco-MiniLM-L-6-v2}} obtiene
    mayor calidad agregada y menor complejidad computacional. Por tanto, no existe
    una justificación calidad-coste para seleccionar \texttt{{cross-encoder/ms-marco-MiniLM-L-12-v2}} en
    esta fase.
    """.strip())

        path.write_text(text + "\n", encoding="utf-8")

    def score_for(ranking: pd.DataFrame, combo: str) -> float:
        match = ranking.loc[ranking["combo"] == combo, "score"]
        if match.empty:
            raise ValueError(f"Missing combo in ranking: {combo}")
        return float(match.iloc[0])

    def write_bge_discard_table(ranking: pd.DataFrame) -> None:
        path = out_dir / "discard_bge_base_evidence.tex"

        multi_full = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        bge_full = "BAAI/bge-base-en-v1.5"

        multi_short = r"\texttt{multi-qa-MiniLM-L6}"
        bge_short = r"\texttt{bge-base}"

        multi_combos = ranking[ranking["combo"].str.startswith("multi-qa-mini__")]
        bge_combos = ranking[ranking["combo"].str.startswith("bge-base__")]

        multi_mean = float(multi_combos["score"].mean())
        bge_mean = float(bge_combos["score"].mean())

        multi_best = float(multi_combos["score"].max())
        bge_best = float(bge_combos["score"].max())

        rows = [
            (
                "Media sobre los tres re-rankers",
                multi_mean,
                bge_mean,
                rf"{multi_short} obtiene +{fmt_score(multi_mean - bge_mean)} puntos de media.",
            ),
            (
                "Mejor combinación disponible",
                multi_best,
                bge_best,
                rf"El mejor {bge_short} queda -{fmt_score(multi_best - bge_best)} puntos por debajo del mejor resultado global.",
            ),
            (
                r"Con \texttt{ms-marco-MiniLM-L-6-v2}",
                score_for(ranking, "multi-qa-mini__ms-marco-L6"),
                score_for(ranking, "bge-base__ms-marco-L6"),
                rf"{multi_short} gana +{fmt_score(score_for(ranking, 'multi-qa-mini__ms-marco-L6') - score_for(ranking, 'bge-base__ms-marco-L6'))} puntos en comparación emparejada.",
            ),
            (
                r"Con \texttt{ms-marco-MiniLM-L-12-v2}",
                score_for(ranking, "multi-qa-mini__ms-marco-L12"),
                score_for(ranking, "bge-base__ms-marco-L12"),
                rf"{multi_short} gana +{fmt_score(score_for(ranking, 'multi-qa-mini__ms-marco-L12') - score_for(ranking, 'bge-base__ms-marco-L12'))} puntos en comparación emparejada.",
            ),
            (
                r"Con \texttt{bge-reranker-base}",
                score_for(ranking, "multi-qa-mini__bge-reranker"),
                score_for(ranking, "bge-base__bge-reranker"),
                "La diferencia es marginal, pero ambas variantes quedan por debajo de la combinación seleccionada.",
            ),
        ]

        lines: list[str] = []
        lines.append(r"\begin{table}[H]")
        lines.append(r"\centering")
        lines.append(r"\scriptsize")
        lines.append(r"\setlength{\tabcolsep}{3pt}")
        lines.append(r"\renewcommand{\arraystretch}{1.05}")
        lines.append(r"\begin{adjustbox}{max width=\textwidth}")
        lines.append(r"\begin{tabularx}{\textwidth}{")
        lines.append(r">{\raggedright\arraybackslash}p{0.31\textwidth}")
        lines.append(r">{\centering\arraybackslash}p{0.13\textwidth}")
        lines.append(r">{\centering\arraybackslash}p{0.13\textwidth}")
        lines.append(r">{\raggedright\arraybackslash}X")
        lines.append(r"}")
        lines.append(r"\toprule")
        lines.append(
            r"\textbf{Comparación} & "
            r"\textbf{\shortstack{MultiQA\\MiniLM-L6}} & "
            r"\textbf{\shortstack{BGE\\base}} & "
            r"\textbf{Lectura} \\"
        )
        lines.append(r"\midrule")

        for i, (label, multi_value, bge_value, reading) in enumerate(rows):
            lines.append(
                f"{label} & {fmt_score(multi_value)} & {fmt_score(bge_value)} & {reading} \\\\"
            )
            if i != len(rows) - 1:
                lines.append(r"\midrule")

        lines.append(r"\bottomrule")
        lines.append(r"\end{tabularx}")
        lines.append(r"\end{adjustbox}")
        lines.append(r"\caption{Evidencia agregada para descartar \texttt{BAAI/bge-base-en-v1.5} como modelo de recuperación del cribado medio.}")
        lines.append(r"\label{tab:discard_bge_base_evidence}")
        lines.append(
            rf"\par\vspace{{2pt}}\noindent\scriptsize\emph{{Nota.}} "
            rf"\texttt{{multi-qa-MiniLM-L6}} corresponde a \texttt{{{multi_full}}}; "
            rf"\texttt{{bge-base}} corresponde a \texttt{{{bge_full}}}."
        )
        lines.append(r"\end{table}")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    def write_bge_discard_text(ranking: pd.DataFrame) -> None:
        path = out_dir / "discard_bge_base_interpretation.tex"

        best_global = float(ranking["score"].max())
        best_bge = float(ranking[ranking["combo"].str.startswith("bge-base__")]["score"].max())
        gap = best_global - best_bge

        l6_gap = score_for(ranking, "multi-qa-mini__ms-marco-L6") - score_for(
            ranking, "bge-base__ms-marco-L6"
        )
        l12_gap = score_for(ranking, "multi-qa-mini__ms-marco-L12") - score_for(
            ranking, "bge-base__ms-marco-L12"
        )

        text = (rf"""
    La Tabla~\ref{{tab:discard_bge_base_evidence}} justifica el descarte de
    \texttt{{BAAI/bge-base-en-v1.5}} como modelo de recuperación para los
    experimentos restantes. Su mejor combinación alcanza {fmt_score(
            best_bge)} puntos,
    {fmt_score(gap)} puntos por debajo de la combinación seleccionada. Además, en
    las comparaciones emparejadas con re-rankers MS MARCO, \texttt{{sentence-transformers/multi-qa-MiniLM-L6-cos-v1}}
    supera a \texttt{{BAAI/bge-base-en-v1.5}} tanto con L6 (+{fmt_score(l6_gap)} puntos) como
    con L12 (+{fmt_score(l12_gap)} puntos). Por tanto, mantener
    \texttt{{BAAI/bge-base-en-v1.5}} en el cribado medio aumentaría el coste experimental sin
    aportar una hipótesis competitiva frente a \texttt{{sentence-transformers/multi-qa-MiniLM-L6-cos-v1}} +
    \texttt{{cross-encoder/ms-marco-MiniLM-L-6-v2}}.
    """.strip())

        path.write_text(text + "\n", encoding="utf-8")

    def compact_llm_label(llm: str) -> str:
        if llm == "llama3.2:latest":
            return r"\shortstack{llama3.2\\Puntuación/Clasificación}"
        if llm == "llama3:8b":
            return r"\shortstack{llama3:8b\\Puntuación/Clasificación}"
        if llm == "mistral:7b":
            return r"\shortstack{mistral:7b\\Puntuación/Clasificación}"
        return rf"\shortstack{{{llm}\\Puntuación/Clasificación}}"

    def write_matrix_table(ranking: pd.DataFrame, by_combo_llm: pd.DataFrame) -> None:
        path = out_dir / "combo_score_matrix_by_llm_compact.tex"

        llms = [llm for llm in LLM_ORDER if llm in set(by_combo_llm["llm"])]
        llms += [llm for llm in sorted(by_combo_llm["llm"].unique()) if llm not in llms]

        matrix = by_combo_llm.set_index(["combo", "llm"])

        col_spec = "lcc" + ("c" * len(llms))

        lines: list[str] = []
        lines.append(r"\begin{table}[H]")
        lines.append(r"\centering")
        lines.append(r"\scriptsize")
        lines.append(r"\setlength{\tabcolsep}{3pt}")
        lines.append(r"\begin{adjustbox}{max width=0.94\textwidth}")
        lines.append(rf"\begin{{tabular}}{{{col_spec}}}")
        lines.append(r"\toprule")

        headers = [
            r"\textbf{Retriever + re-ranker}",
            r"\textbf{Clasificación agregada}",
            r"\textbf{Puntuación agregada}",
        ]
        headers += [rf"\textbf{{{compact_llm_label(llm)}}}" for llm in llms]
        lines.append(" & ".join(headers) + r" \\")
        lines.append(r"\midrule")

        for _, row in ranking.iterrows():
            combo = row["combo"]
            retriever, reranker = split_combo(combo)
            combo_label = rf"\texttt{{{RETRIEVER_LABELS.get(retriever, retriever)} + {RERANKER_LABELS.get(reranker, reranker)}}}"

            cells = [
                combo_label,
                str(int(row["rank"])),
                fmt_score(row["score"]),
            ]

            for llm in llms:
                if (combo, llm) not in matrix.index:
                    cells.append("--")
                    continue
                item = matrix.loc[(combo, llm)]
                cells.append(f"{fmt_score(float(item['score']))} / {int(item['rank_within_llm'])}")

            lines.append(" & ".join(cells) + r" \\")

        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(r"\end{adjustbox}")
        lines.append(r"\caption{Matriz comparativa de combinaciones retriever$\times$re-ranker por modelo generativo.}")
        lines.append(r"\label{tab:combo_score_matrix_by_llm}")
        lines.append(r"\par\vspace{2pt}")
        lines.append(r"\begin{minipage}{0.94\textwidth}")
        lines.append(
            r"\scriptsize\emph{Nota.} En cada celda de modelo se muestra "
            r"\emph{puntuación/clasificación}: la puntuación ponderada obtenida por la "
            r"combinación y su posición relativa dentro de ese modelo "
            r"generativo. La combinación seleccionada debe leerse como una "
            r"decisión instrumental del cribado retriever$\times$re-ranker, "
            r"no como una comparativa final entre modelos generativos. "
            r"\texttt{multi-qa-MiniLM-L6} corresponde a "
            r"\texttt{sentence-transformers/\allowbreak multi-qa-MiniLM-L6-cos-v1}; "
            r"\texttt{bge-base} corresponde a "
            r"\texttt{BAAI/\allowbreak bge-base-en-v1.5}; "
            r"\texttt{ms-marco-L6} corresponde a "
            r"\texttt{cross-encoder/\allowbreak ms-marco-MiniLM-L-6-v2}; "
            r"\texttt{ms-marco-L12} corresponde a "
            r"\texttt{cross-encoder/\allowbreak ms-marco-MiniLM-L-12-v2}; "
            r"\texttt{bge-reranker} corresponde a "
            r"\texttt{BAAI/\allowbreak bge-reranker-base}."
        )
        lines.append(r"\end{minipage}")
        lines.append(r"\end{table}")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    def write_chart_interpretation(ranking: pd.DataFrame) -> None:
        path = out_dir / "combo_chart_interpretation.tex"

        top = ranking.iloc[0]
        best_bge = ranking[ranking["combo"].str.startswith("bge-base__")].iloc[0]
        gap = float(top["score"] - best_bge["score"])

        text = rf"""
    La Figura~\ref{{fig:combo_quality_score_ranking_triviaqa}} refuerza visualmente
    la misma decisión: las primeras posiciones corresponden a combinaciones con
    \texttt{{sentence-transformers/multi-qa-MiniLM-L6-cos-v1}}, mientras que la mejor combinación con
    \texttt{{BAAI/bge-base-en-v1.5}} queda por debajo del mejor resultado por
    {fmt_score(gap)} puntos. En consecuencia, el cribado medio continúa con una
    única combinación retriever$\times$re-ranker: \texttt{{sentence-transformers/multi-qa-MiniLM-L6-cos-v1}} +
    \texttt{{cross-encoder/ms-marco-MiniLM-L-6-v2}}.
    """.strip()

        path.write_text(text + "\n", encoding="utf-8")

    def main() -> int:
        out_dir.mkdir(parents=True, exist_ok=True)

        sel = load_selection_rows()
        ranking, by_combo_llm = compute_combo_ranking(sel)

        write_combo_ranking_table(ranking)
        write_combo_selection_text(ranking, by_combo_llm)
        write_bge_discard_table(ranking)
        write_bge_discard_text(ranking)
        write_matrix_table(ranking, by_combo_llm)
        write_chart_interpretation(ranking)

        print(f"Generated thesis combo artifacts in: {out_dir}")
        return 0


    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        logger.warning(
            "Skipping compact thesis artifacts under %s: %s: %s",
            base_dir, type(exc).__name__, exc,
        )
    except (OSError, ImportError) as exc:
        logger.error(
            "Failed to generate compact thesis artifacts under %s: %s: %s",
            base_dir, type(exc).__name__, exc,
        )


def main(argv: list[str] | None = None) -> int:

    args: argparse.Namespace = parse_args(argv)


    if args.cache_dir is None:
        args.cache_dir = (
            Path(__file__).resolve().parent.parent / ".cache" / "rag" / args.dataset
        )

    LOG_DIR.mkdir(parents=True, exist_ok=True)


    import datetime as _dt
    _run_ts: str = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    _default_log_file: Path = LOG_DIR / "cli_runs" / f"run_{_run_ts}.log"
    cli_log_file: Path = args.log_file if args.log_file is not None else _default_log_file
    _attach_file_logger(cli_log_file)
    if str(cli_log_file) != "/dev/null":

        print(
            f"[run_retriever_comparison] Full log → {cli_log_file}",
            file=sys.stderr,
            flush=True,
        )
        logger.info("Run log file: %s", cli_log_file)

    combos: list[ComboSpec] = _build_combo_grid()


    if args.list_combos:
        print()
        print("=" * 70)
        print("  COMBINATION GRID (retrieval_model × reranker_model)")
        print("=" * 70)
        print(f"  {'#':<3} {'Alias':<32} {'Retriever Model':<42} {'Reranker'}")
        print("-" * 70)
        for i, combo in enumerate(combos, start=1):
            print(
                f"  {i:<3} {combo.alias:<32} {combo.retrieval_model:<42} "
                f"{combo.reranker_model}"
            )
        print()
        print(f"  Total combinations: {len(combos)}")
        print(
            f"  Pipeline configs per combo: {args.configs} "
            f"({len(args.configs)} configs × {args.max_samples} samples = "
            f"{len(args.configs) * args.max_samples} samples per combo)"
        )
        print(
            f"  Total experiments approx: "
            f"{len(combos) * len(args.configs) * args.max_samples}"
        )
        print()
        return 0


    if not args.generate_only:
        logger.info("=" * 70)
        logger.info("  RETRIEVER × RERANKER COMPARISON")
        logger.info("  Combos: %d  |  Configs/combo: %d  |  Samples: %d",
                    len(combos), len(args.configs), args.max_samples)
        logger.info("  Dataset: %s  |  dry-run: %s", args.dataset, args.dry_run)
        logger.info("=" * 70)

        t_total_start: float = time.perf_counter()


        cache_manager: Any = None
        if (args.use_cache or args.cached_contexts
                or args.cached_only or args.refresh_cache):
            from src.cache import CacheManager as _CM
            cache_manager = _CM(args.cache_dir, refresh=args.refresh_cache)
            logger.info(
                "Cache: dir=%s refresh=%s cached_contexts=%s cached_only=%s",
                args.cache_dir, args.refresh_cache,
                args.cached_contexts, args.cached_only,
            )


            if (
                args.prewarm_cache
                and not args.dry_run
                and not args.cached_only
            ):
                try:
                    _prewarm_combos_before_experiments(
                        cache_manager=cache_manager,
                        combos=combos,
                        config_options=args.configs,
                        dataset=args.dataset,
                        max_samples=args.max_samples,
                    )
                except (RuntimeError, OSError, ImportError) as exc:
                    logger.warning(
                        "Prewarm cache failed (%s: %s). Experiments will "
                        "continue and populate the cache inline.",
                        type(exc).__name__, exc,
                    )

        for i, combo in enumerate(combos, start=1):
            logger.info(
                "[%d/%d] Running combo: %s", i, len(combos), combo.alias
            )
            run_combo(
                combo=combo,
                configs=args.configs,
                max_samples=args.max_samples,
                dry_run=args.dry_run,
                dataset=args.dataset,
                model_label=args.model_label,
                cache_manager=cache_manager,
                cached_only=args.cached_only,
            )

        total_elapsed: float = time.perf_counter() - t_total_start
        logger.info(
            "All combos finished in %.1f s (%.1f min).",
            total_elapsed, total_elapsed / 60.0,
        )


        if not args.skip_eval:
            logger.info("=" * 70)
            logger.info("  PHASE 2 EVALUATION - all combo runs")
            logger.info("  NOTE: ~5 minute wait recommended if rate-limited.")
            logger.info("=" * 70)

            eval_results: dict[str, dict[str, Any]] = evaluate_all_combos(
                combos=combos,
                dry_run=args.dry_run,
            )


            total_pending: int = sum(
                r.get("pending", 0) + r.get("failed", 0)
                for r in eval_results.values()
                if isinstance(r, dict)
            )
            if total_pending > 0:
                print()
                print("=" * 70)
                print(f"  ┌─ [PENDING EVALUATIONS] ──────────────────────────────────────┐")
                print(f"  │  {total_pending} samples pending/failed across all combos.                 │")
                print(f"  │  Wait ~5 minutes to avoid OpenAI rate limits, then run:      │")
                print(f"  └──────────────────────────────────────────────────────────────┘")
                print()
                for combo in combos:
                    if combo.run_dir and combo.run_dir.exists():
                        combo_pending = eval_results.get(combo.alias, {}).get(
                            "pending", 0
                        ) + eval_results.get(combo.alias, {}).get("failed", 0)
                        if combo_pending > 0:
                            print(
                                f"  Combo [{combo.alias}] - {combo_pending} pending:"
                            )
                            print(
                                f"    python -m src.evaluation.run_evaluation"
                                f" --run-dir {combo.run_dir} --pending-only"
                            )
                            print()
                print("=" * 70)
        else:
            logger.info("Skipping evaluation (--skip-eval).")


    logger.info("=" * 70)
    logger.info("  GENERATING COMBO-SELECTION ARTIFACTS")
    logger.info("=" * 70)

    all_generated: list[Path] = []

    if args.generate_only or args.aggregate_existing_combo_runs:
        summaries = _discover_combo_summaries(combos, LOG_DIR)
        summaries = [
            s for s in summaries
            if str(s.get("dataset", "") or "") == args.dataset
        ]
    else:
        summaries = []
        for combo in combos:
            summary = _load_combo_summary(combo)
            if summary is None:
                continue
            summary["combo_alias"] = combo.alias
            summary["experiment_family"] = EXPERIMENT_FAMILY
            summaries.append(summary)

    all_generated.extend(
        generate_combo_selection_artifacts(
            combos=combos,
            output_dir=args.output_dir,
            summaries=summaries,
            diagnostics=args.with_diagnostics,
        )
    )

    generate_detailed_diagnostics = args.with_diagnostics

    if args.aggregate_existing_combo_runs and args.with_diagnostics:
        logger.warning(
            "--with-diagnostics with --aggregate-existing-combo-runs is not used "
            "for detailed per-combo charts because the old diagnostic path only "
            "selects the latest run per combo. Compact aggregate artifacts remain valid."
        )
        generate_detailed_diagnostics = False
    elif args.aggregate_existing_combo_runs:
        generate_detailed_diagnostics = False

    if generate_detailed_diagnostics and args.generate_only:
        _discover_combo_run_dirs(combos, LOG_DIR)


    if generate_detailed_diagnostics:
        diagnostics_dir: Path = (
                args.output_dir
                / "combo_sweep"
                / args.dataset
                / "diagnostics_per_combo"
        )
        diagnostics_dir.mkdir(parents=True, exist_ok=True)

        for combo in combos:
            if not combo.run_dir or not combo.run_dir.exists():
                logger.warning(
                    "Combo '%s' has no run_dir - skipping diagnostic chart generation.",
                    combo.alias,
                )
                continue

            generated: list[Path] = generate_combo_charts(
                combo=combo,
                output_dir=diagnostics_dir,
            )
            all_generated.extend(generated)


    print()
    print("=" * 70)
    print("  COMPARISON COMPLETE")
    print("=" * 70)
    print()
    print(f"  Output:  {args.output_dir}")
    print(f"  Files:   {len(all_generated)}")
    print()
    for p in all_generated:
        print(f"    {p}")
    print()

    print("  For main experiments with winner models, edit these constants in")
    print("  src/pipeline/__init__.py :")
    print()
    print("    RETRIEVAL_MODEL = \"<best retrieval model>\"")
    print("    RERANKER_MODEL  = \"<best reranker model>\"")
    print()
    print("  Then run the full experiment suite:")
    print()
    print("    python3 scripts/run_experiments.py --dataset rag_domain")
    print()
    print("  Then generate thesis charts:")
    print()
    print(f"    python3 scripts/generate_charts.py --dataset {args.dataset} --strategy latest")
    print()
    print("=" * 70)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
