from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import random
import re as _re
import statistics
import time
import uuid as _uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar


logger: logging.Logger = logging.getLogger(__name__)


DEFAULT_LOG_DIR: Path = Path("logs")


SCHEMA_VERSION_V2: str = "2.0"


class PerformanceTimer:


    __slots__: ClassVar[tuple[str, ...]] = (
        "label", "start_time", "end_time", "elapsed_ms",
    )

    def __init__(self, label: str = "") -> None:
        self.label: str = label
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> PerformanceTimer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000.0
        logger.debug("%s: %.2f ms", self.label, self.elapsed_ms)


def format_duration(seconds: float | int | None) -> str:

    if seconds is None or seconds < 0:
        return "0s"
    total: int = int(round(float(seconds)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _slugify_model(model: str | None) -> str:

    if not model:
        return "unknown"
    slug: str = _re.sub(r"[^A-Za-z0-9]+", "_", model).strip("_")
    return slug.lower() or "unknown"


def create_run_id(model: str | None = None) -> str:

    ts: str = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    short: str = _uuid.uuid4().hex[:8]
    return f"run_{ts}_{_slugify_model(model)}_{short}"


def make_eval_item_id(run_id: str, config_name: str, sample_index: int) -> str:

    return f"{run_id}::{config_name}::{int(sample_index):04d}"


def initial_pending_evaluation_metadata(num_samples: int) -> dict[str, Any]:

    return {
        "status": "pending",
        "method": None,
        "model": None,
        "scores_scale": "0_to_100",
        "started_at": None,
        "completed_at": None,
        "num_samples_total": int(num_samples),
        "num_samples_evaluated": 0,
        "num_samples_pending": int(num_samples),
        "num_samples_failed": 0,
        "last_error": None,
    }


def initial_pending_sample_eval() -> dict[str, Any]:

    return {
        "status": "pending",
        "method": None,
        "model": None,
        "batch_mode": None,
        "batch_id": None,
        "batch_custom_id": None,
        "evaluated_at": None,
        "attempt_count": 0,
        "last_error": None,
        "scores": None,
        "judge_notes": None,
    }


@dataclass
class ExperimentLogV2:


    run_id: str = ""
    experiment_id: str = ""
    config_name: str = ""
    config_option: int = 0
    timestamp_start: str = ""
    timestamp_end: str = ""
    elapsed_seconds: float = 0.0
    dataset: str = ""
    num_queries: int = 0
    model: str = ""
    model_size_gb: str = ""
    model_size_category: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)
    evaluation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:

        return {
            "schema_version": SCHEMA_VERSION_V2,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "config_name": self.config_name,
            "config_option": self.config_option,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "elapsed_seconds": round(float(self.elapsed_seconds), 3),
            "elapsed_human": format_duration(self.elapsed_seconds),
            "dataset": self.dataset,
            "num_queries": int(self.num_queries),
            "model": self.model,
            "model_size_gb": self.model_size_gb,
            "model_size_category": self.model_size_category,
            "config": self.config,
            "evaluation": (
                self.evaluation
                or initial_pending_evaluation_metadata(self.num_queries)
            ),
            "metrics": self.metrics,
            "samples": self.samples,
        }

    def save(self, experiments_dir: Path) -> Path:

        experiments_dir.mkdir(parents=True, exist_ok=True)
        path: Path = experiments_dir / f"{self.config_name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("Experimento v2 guardado: %s", path)
        return path


class RunManifest:


    def __init__(
        self,
        run_id: str,
        run_dir: Path,
        dataset: str,
        mode: str,
        model_label: str,
        model_detected: str,
        model_size_gb: str,
        model_size_category: str,
        num_configs_expected: int,
        num_queries_per_config: int,
        run_type: str = "main",
    ) -> None:
        self.run_id: str = run_id
        self.run_dir: Path = run_dir
        now_iso: str = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


        _RUN_TYPE_TO_FAMILY: dict[str, str] = {
            "main": "main_experiment",
            "model_selection": "model_selection",
        }
        experiment_family: str = _RUN_TYPE_TO_FAMILY.get(run_type, "main_experiment")
        self._data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION_V2,
            "run_id": run_id,
            "created_at": now_iso,
            "updated_at": now_iso,
            "dataset": dataset,
            "mode": mode,
            "run_type": run_type,


            "experiment_family": experiment_family,
            "model_label": model_label,
            "model_detected": model_detected,
            "model_size_gb": model_size_gb,
            "model_size_category": model_size_category,
            "num_configs_expected": int(num_configs_expected),
            "num_configs_completed": 0,
            "num_queries_per_config": int(num_queries_per_config),
            "status": "in_progress",
            "experiments": {},
            "summary_path": "summaries/experiment_summary.json",
        }

    @property
    def path(self) -> Path:
        return self.run_dir / "run_manifest.json"

    def save(self) -> Path:
        self._data["updated_at"] = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        return self.path

    def update_config_completed(
        self,
        config_name: str,
        config_option: int,
        elapsed_seconds: float,
        success: bool,
        error_message: str = "",
    ) -> None:
        entry: dict[str, Any] = {
            "config_option": int(config_option),
            "path": f"experiments/{config_name}.json",
            "status": "completed" if success else "failed",
            "evaluation_status": "pending" if success else "skipped",
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "elapsed_human": format_duration(elapsed_seconds),
        }
        if not success and error_message:
            entry["error_message"] = error_message
        self._data["experiments"][config_name] = entry
        if success:
            self._data["num_configs_completed"] = int(
                self._data["num_configs_completed"]
            ) + 1
        self.save()

    def mark_run_evaluation_pending(self) -> None:
        self._data["status"] = "experiments_completed_evaluation_pending"
        self.save()

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


class ExperimentRunner:


    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR) -> None:
        self.log_dir: Path = log_dir

    def run_collect_only(
        self,
        results: list[Any],
        config_name: str,
        config_option: int,
        config: dict[str, Any],
        run_id: str,
        dataset: str,
        ground_truths: list[str] | None = None,
        timestamp_start: str | None = None,
        timestamp_end: str | None = None,
        elapsed_seconds: float = 0.0,
    ) -> ExperimentLogV2:

        ts_start: str = timestamp_start or time.strftime("%Y-%m-%dT%H:%M:%S")
        ts_end: str = timestamp_end or time.strftime("%Y-%m-%dT%H:%M:%S")
        experiment_id: str = (
            f"{config_name}_{time.strftime('%Y%m%d_%H%M%S')}"
        )

        log_v2: ExperimentLogV2 = ExperimentLogV2(
            run_id=run_id,
            experiment_id=experiment_id,
            config_name=config_name,
            config_option=int(config_option),
            timestamp_start=ts_start,
            timestamp_end=ts_end,
            elapsed_seconds=float(elapsed_seconds),
            dataset=dataset,
            num_queries=len(results),
            config=config,
            evaluation=initial_pending_evaluation_metadata(len(results)),
        )


        for r in results:
            meta: dict[str, Any] = getattr(r, "metadata", {}) or {}
            if meta.get("model"):
                log_v2.model = meta.get("model", "")
                log_v2.model_size_gb = str(meta.get("model_size_gb", ""))
                log_v2.model_size_category = meta.get(
                    "model_size_category", "",
                )
                break


        latencies: list[float] = []
        query_embedding_times: list[float] = []
        retrieval_times: list[float] = []
        reranking_times: list[float] = []
        context_selection_times: list[float] = []
        prompt_build_times: list[float] = []
        generation_times: list[float] = []
        answer_lengths: list[int] = []

        for r in results:
            timings: dict[str, float] = getattr(r, "timings", {}) or {}


            query_embedding: float = float(timings.get("query_embedding_ms", 0.0) or 0.0)
            retrieval: float = float(timings.get("retrieval_ms", 0.0) or 0.0)
            reranking: float = float(timings.get("reranking_ms", 0.0) or 0.0)
            context_selection: float = float(timings.get("context_selection_ms", 0.0) or 0.0)
            prompt_build: float = float(timings.get("prompt_build_ms", 0.0) or 0.0)
            generation: float = float(timings.get("llm_generation_ms", 0.0) or 0.0)
            total: float = float(timings.get("total_pipeline_ms", 0.0) or 0.0)


            if total <= 0.0:
                retrieval_total: float = float(
                    timings.get("retrieval_total_ms", 0.0) or 0.0
                )
                total = retrieval_total + prompt_build + generation

            latencies.append(total)
            query_embedding_times.append(query_embedding)
            retrieval_times.append(retrieval)
            reranking_times.append(reranking)
            context_selection_times.append(context_selection)
            prompt_build_times.append(prompt_build)
            generation_times.append(generation)

            ans_text: str = getattr(r, "answer", "") or ""
            answer_lengths.append(len(ans_text.split()))

        def _add_metric(
            name: str,
            value: float,
            extra: dict[str, Any] | None = None,
        ) -> None:
            entry: dict[str, Any] = {
                "tag": "THESIS_METRIC",
                "metric": name,
                "value": round(float(value), 4),
                "config": config_name,
            }
            if extra:
                entry.update(extra)
            log_v2.metrics.append(entry)

        if latencies:
            _add_metric(
                "latency_mean_ms",
                statistics.mean(latencies),
                {
                    "std": round(_safe_stdev(latencies), 4),
                    "min": round(min(latencies), 4),
                    "max": round(max(latencies), 4),
                    "method": "pipeline_timing",
                },
            )
        if latencies:
            _add_metric(
                "total_pipeline_mean_ms",
                statistics.mean(latencies),
                {
                    "std": round(_safe_stdev(latencies), 4),
                    "min": round(min(latencies), 4),
                    "max": round(max(latencies), 4),
                    "method": "pipeline_timing",
                },
            )


        if any(v > 0.0 for v in query_embedding_times):
            _add_metric(
                "query_embedding_time_mean_ms",
                statistics.mean(query_embedding_times),
                {
                    "std": round(_safe_stdev(query_embedding_times), 4),
                    "method": "pipeline_timing",
                },
            )
        if any(v > 0.0 for v in retrieval_times):
            _add_metric(
                "retrieval_time_mean_ms",
                statistics.mean(retrieval_times),
                {
                    "std": round(_safe_stdev(retrieval_times), 4),
                    "method": "pipeline_timing",
                    "note": "pure ANN/vector-store lookup only (retrieval_ms)",
                },
            )
        if any(v > 0.0 for v in reranking_times):
            _add_metric(
                "reranking_time_mean_ms",
                statistics.mean(reranking_times),
                {
                    "std": round(_safe_stdev(reranking_times), 4),
                    "method": "pipeline_timing",
                },
            )
        if any(v > 0.0 for v in context_selection_times):
            _add_metric(
                "context_selection_time_mean_ms",
                statistics.mean(context_selection_times),
                {
                    "std": round(_safe_stdev(context_selection_times), 4),
                    "method": "pipeline_timing",
                },
            )

        if prompt_build_times:
            _add_metric(
                "prompt_build_time_mean_ms",
                statistics.mean(prompt_build_times),
                {
                    "std": round(_safe_stdev(prompt_build_times), 4),
                    "method": "pipeline_timing",
                },
            )
        if generation_times:
            _add_metric(
                "generation_time_mean_ms",
                statistics.mean(generation_times),
                {
                    "std": round(_safe_stdev(generation_times), 4),
                    "method": "pipeline_timing",
                },
            )
        if answer_lengths:
            _add_metric(
                "answer_length_tokens_mean",
                float(statistics.mean(answer_lengths)),
                {
                    "std": round(
                        _safe_stdev([float(x) for x in answer_lengths]), 4,
                    ),
                    "min": int(min(answer_lengths)),
                    "max": int(max(answer_lengths)),
                    "method": "pipeline_metadata",
                },
            )


        try:
            import resource
            mem_kb: int = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            _add_metric("memory_peak_mb", mem_kb / 1024.0, {"method": "rusage"})
        except (ImportError, AttributeError):
            pass

        _add_metric("num_samples", float(len(results)))


        for i, r in enumerate(results):
            gt: str = (
                ground_truths[i]
                if (ground_truths and i < len(ground_truths))
                else ""
            )
            timings = getattr(r, "timings", {}) or {}
            meta = getattr(r, "metadata", {}) or {}
            contexts: list[str] = list(getattr(r, "contexts", []) or [])
            context_chars: int = sum(len(c) for c in contexts)

            sample: dict[str, Any] = {
                "index": i,
                "eval_item_id": make_eval_item_id(run_id, config_name, i),
                "config_name": config_name,
                "question": getattr(r, "query", ""),
                "answer": getattr(r, "answer", ""),
                "prompt": getattr(r, "prompt", ""),
                "ground_truth": gt,
                "contexts": contexts,


                "context_sources": list(meta.get("context_sources", []) or []),
                "num_contexts": len(contexts),
                "num_chunks_retrieved": int(meta.get("num_chunks_retrieved", 0) or 0),
                "num_chunks_reranked": int(meta.get("num_chunks_reranked", 0) or 0),
                "num_chunks_final": int(meta.get("num_chunks_final", len(contexts)) or len(contexts)),
                "context_chars_total": context_chars,
                "context_tokens_est": int(meta.get("context_tokens_est", 0) or 0),
                "avg_chunk_size_chars": float(meta.get("avg_chunk_size_chars", 0.0) or 0.0),
                "source_files_used": list(meta.get("source_files_used", []) or []),
                "chunk_ids_final": list(meta.get("chunk_ids_final", []) or []),
                "chunker": str(meta.get("chunker", config.get("chunker", ""))),
                "retriever_type": str(meta.get("retriever_type", config.get("retriever", ""))),
                "reranker": str(config.get("reranker", "")),
                "prompt_version": str(meta.get("prompt_version", config.get("prompt_version", ""))),
                "context_selection_mode": str(meta.get("context_selection_mode", "top_n")),
                "neighbor_expansion_used": bool(meta.get("neighbor_expansion_used", False)),
                "retrieval_score_type": str(meta.get("retrieval_score_type", "")),
                "reranker_score_type": str(meta.get("reranker_score_type", "")),

                "retrieval_scores": list(meta.get("retrieval_scores", []) or []),
                "reranker_scores": list(meta.get("reranker_scores", []) or []),

                "retrieval_top_k_details": list(meta.get("retrieval_top_k_details", []) or []),
                "timings_ms": {


                    "retrieval": round(float(timings.get("retrieval_total_ms", 0.0)), 2),
                    "reranking": round(float(timings.get("reranking_ms", 0.0)), 2),
                    "prompt_build": round(float(timings.get("prompt_build_ms", 0.0)), 2),
                    "llm_generation": round(float(timings.get("llm_generation_ms", 0.0)), 2),

                    "total_pipeline": round(total, 2),
                },
                "model": meta.get("model", ""),
                "model_size_gb": str(meta.get("model_size_gb", "")),
                "model_size_category": meta.get("model_size_category", ""),
                "tokens_prompt": int(meta.get("tokens_prompt", 0) or 0),
                "tokens_generated": int(meta.get("tokens_generated", 0) or 0),
                "eval": initial_pending_sample_eval(),
            }
            log_v2.samples.append(sample)

        logger.info(
            "[Phase1] Experimento '%s' recolectado: %d muestras, "
            "latency_mean=%.1f ms, evaluation=pending",
            config_name,
            len(results),
            statistics.mean(latencies) if latencies else 0.0,
        )
        return log_v2


def generate_summary_v2(
    run_id: str,
    run_dir: Path,
    dataset: str,
    mode: str,
    model_label: str,
    model_detected: str,
    model_size_gb: str,
    model_size_category: str,
    timestamp_start: str,
    timestamp_end: str,
    total_elapsed_seconds: float,
    experiment_logs: list[ExperimentLogV2],
    failed_configs: list[tuple[str, str]] | None = None,
) -> Path:

    summaries_dir: Path = run_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    experiments_block: dict[str, Any] = {}
    for log in experiment_logs:
        perf: dict[str, float] = {}
        for m in log.metrics:
            name: str = m.get("metric", "")
            if name in PERFORMANCE_METRIC_NAMES:
                perf[name] = round(float(m.get("value", 0.0)), 4)
        experiments_block[log.config_name] = {
            "config_option": log.config_option,
            "status": "completed",
            "elapsed_seconds": round(float(log.elapsed_seconds), 3),
            "elapsed_human": format_duration(log.elapsed_seconds),
            "num_queries": int(log.num_queries),
            "performance_metrics": perf,
            "quality_metrics": {},
            "eval_pending_count": int(log.num_queries),
            "eval_failed_count": 0,
            "evaluation_status": "pending",
        }
    for config_name, error_message in (failed_configs or []):
        experiments_block.setdefault(config_name, {
            "status": "failed",
            "error_message": error_message,
            "performance_metrics": {},
            "quality_metrics": {},
            "eval_pending_count": 0,
            "eval_failed_count": 0,
            "evaluation_status": "skipped",
        })

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V2,
        "report_type": "experiment_summary",
        "run_id": run_id,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "total_elapsed_seconds": round(float(total_elapsed_seconds), 3),
        "total_elapsed_human": format_duration(total_elapsed_seconds),
        "mode": mode,
        "dataset": dataset,
        "model_label": model_label,
        "model_detected": model_detected,
        "model_size_gb": model_size_gb,
        "model_size_category": model_size_category,
        "evaluation": {
            "status": "pending",
            "method": None,
            "model": None,
            "scores_scale": "0_to_100",
        },
        "experiments": experiments_block,
    }

    summary_path: Path = summaries_dir / "experiment_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


    md_lines: list[str] = [
        f"# Resumen de ejecución `{run_id}`",
        "",
        f"- Inicio: `{timestamp_start}`",
        f"- Fin: `{timestamp_end}`",
        f"- Duración total: **{format_duration(total_elapsed_seconds)}** "
        f"({total_elapsed_seconds:.1f} s)",
        f"- Dataset: `{dataset}`",
        f"- Modo: `{mode}`",
        f"- Modelo (label): `{model_label}` - detectado: `{model_detected}`",
        "- Estado de evaluación: **pending** (se ejecuta en Phase 2)",
        "",
        "## Configuraciones",
        "",
        "| Config | Estado | Muestras | Latencia media (ms) | Duración |",
        "|---|---|---|---|---|",
    ]
    for name, info in experiments_block.items():
        perf = info.get("performance_metrics", {})
        md_lines.append(
            f"| `{name}` | {info.get('status', '?')} | "
            f"{info.get('num_queries', 0)} | "
            f"{perf.get('latency_mean_ms', 0.0):.1f} | "
            f"{info.get('elapsed_human', '-')} |"
        )
    human_path: Path = summaries_dir / "experiment_summary_human.md"
    with open(human_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    logger.info("Resumen v2 guardado: %s", summary_path)
    return summary_path


def append_to_run_index(
    logs_root: Path,
    run_id: str,
    dataset: str,
    mode: str,
    model_label: str,
    model_detected: str,
    timestamp_start: str,
    timestamp_end: str,
    num_configs_completed: int,
    num_configs_expected: int,
    summary_relative_path: str,
    run_type: str = "main",
) -> Path:

    index_dir: Path = logs_root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path: Path = index_dir / "run_index.jsonl"
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V2,
        "run_id": run_id,
        "dataset": dataset,
        "mode": mode,
        "model_label": model_label,
        "model_detected": model_detected,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "num_configs_completed": int(num_configs_completed),
        "num_configs_expected": int(num_configs_expected),
        "summary_path": summary_relative_path,
        "evaluation_status": "pending",
        "run_type": run_type,
    }
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return index_path


def _safe_stdev(values: list[float]) -> float:

    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


from src.evaluation.run_evaluation import (
    evaluate_run,
    collect_unresolved_eval_items,
    regenerate_summary_for_run,
)


from src.evaluation.schemas import (
    PERFORMANCE_METRIC_NAMES,
)


_COMPLETED_STATUSES: frozenset[str] = frozenset({"completed"})
_PENDING_STATUSES: frozenset[str] = frozenset({"pending", "retry_pending"})
_FAILED_STATUSES: frozenset[str] = frozenset({"failed", "error"})


def recompute_llm_eval_metrics(
    experiment_json: dict[str, Any],
) -> dict[str, Any]:

    config_name: str = experiment_json.get("config_name", "unknown")
    samples: list[dict[str, Any]] = experiment_json.get("samples", [])
    model: str = (
        experiment_json.get("evaluation", {}).get("model") or "unknown"
    )


    old_metrics: list[dict[str, Any]] = experiment_json.get("metrics", [])
    performance_metrics: list[dict[str, Any]] = [
        m for m in old_metrics
        if m.get("metric") in PERFORMANCE_METRIC_NAMES
        or m.get("method") in ("pipeline_timing", "pipeline_metadata", "rusage")
    ]


    completed_samples: list[dict[str, Any]] = [
        s for s in samples
        if s.get("eval", {}).get("status") in _COMPLETED_STATUSES
        and s.get("eval", {}).get("scores") is not None
    ]
    pending_count: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status") in _PENDING_STATUSES
    )
    failed_count: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status") in _FAILED_STATUSES
    )
    batch_count: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status") in (
            STATUS_BATCH_SUBMITTED, STATUS_BATCH_RUNNING
        )
    )
    n_evaluated: int = len(completed_samples)
    n_total: int = len(samples)

    if batch_count > 0:
        logger.info(
            "[metrics] Config '%s': %d/%d samples completed, "
            "%d pending, %d in-batch (awaiting async results), %d failed.",
            config_name, n_evaluated, n_total,
            pending_count, batch_count, failed_count,
        )
    else:
        logger.info(
            "[metrics] Config '%s': %d/%d samples completed, %d pending, %d failed.",
            config_name, n_evaluated, n_total, pending_count, failed_count,
        )

    new_quality_metrics: list[dict[str, Any]] = []

    if n_evaluated == 0:


        logger.info(
            "[metrics] Config '%s': no completed samples, skipping quality metric computation.",
            config_name,
        )
        experiment_json["metrics"] = performance_metrics
        return experiment_json

    def _add(
        metric_name: str,
        value: float,
        extra: dict[str, Any] | None = None,
    ) -> None:

        entry: dict[str, Any] = {
            "tag": "THESIS_METRIC",
            "metric": metric_name,
            "value": round(float(value), 4),
            "config": config_name,
            "method": "openai_llm_judge",
            "model": model,
            "n_evaluated": n_evaluated,
            "n_pending": pending_count,
            "scores_scale": "0_to_100",
        }
        if extra:
            entry.update(extra)
        new_quality_metrics.append(entry)


    score_keys: tuple[str, ...] = (
        "correctness",
        "faithfulness",
        "answer_relevance",
        "context_support",
        "refusal_quality",
        "overall",
    )
    metric_suffixes: dict[str, str] = {
        k: f"{k}_mean" for k in score_keys
    }

    for score_key, metric_name in metric_suffixes.items():
        values: list[float] = [
            float(s["eval"]["scores"][score_key])
            for s in completed_samples
            if s["eval"].get("scores") and score_key in s["eval"]["scores"]
        ]
        if not values:
            continue
        mean_val: float = statistics.mean(values)
        std_val: float = _safe_stdev(values)
        _add(
            metric_name,
            mean_val,
            {"std": round(std_val, 4)},
        )


    notes_list: list[dict[str, Any]] = [
        s["eval"].get("judge_notes") or {}
        for s in completed_samples
    ]

    def _rate(flag: str) -> float:

        trues: int = sum(1 for n in notes_list if n.get(flag, False))
        return round((trues / n_evaluated) * 100.0, 4) if n_evaluated else 0.0


    _add("contradiction_rate", _rate("has_contradiction"))
    _add("refusal_rate", _rate("is_refusal"))
    _add("correct_refusal_rate", _rate("is_correct_refusal"))
    _add("false_refusal_rate", _rate("is_false_refusal"))


    _add("answer_accuracy", _rate("answer_correct"))
    _add("context_sufficiency_rate", _rate("context_sufficient"))
    _add("faithfulness_rate", _rate("answer_supported_by_context"))


    _OVERCONF_RELEVANCE_THRESHOLD: float = 70.0
    _n_overconfident: int = sum(
        1
        for s in completed_samples
        if (
            not (s["eval"].get("judge_notes") or {}).get("answer_correct", False)
            and not (s["eval"].get("judge_notes") or {}).get("is_refusal", False)
            and not (s["eval"].get("judge_notes") or {}).get("context_sufficient", False)
            and float((s["eval"].get("scores") or {}).get("answer_relevance", 0.0))
            >= _OVERCONF_RELEVANCE_THRESHOLD
        )
    )
    _add(
        "overconfidence_rate",
        round((_n_overconfident / n_evaluated) * 100.0, 4) if n_evaluated else 0.0,
    )


    failure_types: list[str] = [
        str(n.get("failure_type", "")) for n in notes_list
    ]

    def _failure_rate(ftype: str) -> float:

        count: int = sum(1 for f in failure_types if f == ftype)
        return round((count / n_evaluated) * 100.0, 4) if n_evaluated else 0.0

    _add("retrieval_failure_rate", _failure_rate("retrieval_failure"))
    _add("generation_failure_rate", _failure_rate("generation_failure"))
    _add("combined_failure_rate", _failure_rate("both"))
    _add("uncertain_rate", _failure_rate("uncertain"))


    eval_completion_rate: float = (
        round((n_evaluated / n_total) * 100.0, 4) if n_total else 0.0
    )
    _add("eval_completion_rate", eval_completion_rate)
    _add("eval_pending_count", float(pending_count))
    _add("eval_failed_count", float(failed_count))


    experiment_json["metrics"] = performance_metrics + new_quality_metrics

    logger.info(
        "[metrics] Config '%s': wrote %d quality metrics.",
        config_name, len(new_quality_metrics),
    )
    return experiment_json


STATUS_PENDING: str = "pending"
STATUS_COMPLETED: str = "completed"
STATUS_RETRY_PENDING: str = "retry_pending"
STATUS_FAILED: str = "failed"
STATUS_BATCH_SUBMITTED: str = "batch_submitted"
STATUS_BATCH_RUNNING: str = "batch_running"

METHOD_SYNC: str = "openai_responses_structured_outputs"


DEFAULT_EVAL_MODEL: str = "gpt-5.4-mini"
DEFAULT_SYNC_BATCH_SIZE: int = 10
DEFAULT_SYNC_BATCH_SIZE_MAX: int = 20
DEFAULT_MAX_SYNC_RETRIES: int = 3
DEFAULT_RETRY_BASE_SLEEP: float = 5.0
DEFAULT_RETRY_MAX_SLEEP: float = 60.0


_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 503})


def _get_eval_settings() -> dict[str, Any]:

    try:
        from src.config_loader import get_config
        api_key: str = get_config("OPENAI_API_KEY", "")
        model: str = get_config("OPENAI_EVAL_MODEL", DEFAULT_EVAL_MODEL)
        batch_size: int = int(
            get_config("OPENAI_EVAL_SYNC_BATCH_SIZE", str(DEFAULT_SYNC_BATCH_SIZE))
        )
        batch_size_max: int = int(
            get_config(
                "OPENAI_EVAL_SYNC_BATCH_SIZE_MAX",
                str(DEFAULT_SYNC_BATCH_SIZE_MAX),
            )
        )
        max_retries: int = int(
            get_config(
                "OPENAI_EVAL_MAX_SYNC_RETRIES", str(DEFAULT_MAX_SYNC_RETRIES)
            )
        )
        retry_base: float = float(
            get_config(
                "OPENAI_EVAL_RETRY_BASE_SLEEP_SECONDS",
                str(DEFAULT_RETRY_BASE_SLEEP),
            )
        )
        retry_max: float = float(
            get_config(
                "OPENAI_EVAL_RETRY_MAX_SLEEP_SECONDS",
                str(DEFAULT_RETRY_MAX_SLEEP),
            )
        )
        async_fallback: bool = (
            get_config("OPENAI_EVAL_ASYNC_BATCH_FALLBACK", "true").lower()
            == "true"
        )
    except ImportError:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        model = os.environ.get("OPENAI_EVAL_MODEL", DEFAULT_EVAL_MODEL)
        batch_size = int(
            os.environ.get(
                "OPENAI_EVAL_SYNC_BATCH_SIZE", str(DEFAULT_SYNC_BATCH_SIZE)
            )
        )
        batch_size_max = int(
            os.environ.get(
                "OPENAI_EVAL_SYNC_BATCH_SIZE_MAX",
                str(DEFAULT_SYNC_BATCH_SIZE_MAX),
            )
        )
        max_retries = int(
            os.environ.get(
                "OPENAI_EVAL_MAX_SYNC_RETRIES", str(DEFAULT_MAX_SYNC_RETRIES)
            )
        )
        retry_base = float(
            os.environ.get(
                "OPENAI_EVAL_RETRY_BASE_SLEEP_SECONDS",
                str(DEFAULT_RETRY_BASE_SLEEP),
            )
        )
        retry_max = float(
            os.environ.get(
                "OPENAI_EVAL_RETRY_MAX_SLEEP_SECONDS",
                str(DEFAULT_RETRY_MAX_SLEEP),
            )
        )
        async_fallback = (
            os.environ.get("OPENAI_EVAL_ASYNC_BATCH_FALLBACK", "true").lower()
            == "true"
        )

    return {
        "api_key": api_key,
        "model": model,
        "sync_batch_size": min(max(1, batch_size), batch_size_max),
        "sync_batch_size_max": batch_size_max,
        "max_retries": max_retries,
        "retry_base_sleep": retry_base,
        "retry_max_sleep": retry_max,
        "async_fallback": async_fallback,
    }


def _validate_batch_response(
    parsed: dict[str, Any],
    expected_ids: list[str],
) -> str | None:

    n: int = len(expected_ids)

    received_count: int = parsed.get("received_count", -1)
    if received_count != n:
        return (
            f"received_count mismatch: expected {n}, got {received_count}"
        )

    results: list[dict[str, Any]] = parsed.get("results", [])
    if len(results) != n:
        return (
            f"results length mismatch: expected {n}, got {len(results)}"
        )

    returned_ids: list[str] = [r.get("eval_item_id", "") for r in results]
    expected_set: set[str] = set(expected_ids)
    returned_set: set[str] = set(returned_ids)

    missing: set[str] = expected_set - returned_set
    if missing:
        return f"Missing eval_item_ids: {sorted(missing)}"

    unexpected: set[str] = returned_set - expected_set
    if unexpected:
        return f"Unexpected eval_item_ids: {sorted(unexpected)}"

    if len(returned_ids) != len(returned_set):

        seen: set[str] = set()
        dupes: list[str] = []
        for rid in returned_ids:
            if rid in seen:
                dupes.append(rid)
            seen.add(rid)
        return f"Duplicate eval_item_ids: {dupes}"

    return None


class OpenAIRagJudge:


    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._settings: dict[str, Any] = _get_eval_settings()
        if api_key:
            self._settings["api_key"] = api_key
        if model:
            self._settings["model"] = model
        self._client: Any | None = None

    def _get_client(self) -> Any:

        if self._client is None:
            try:
                import openai
            except ImportError as exc:
                raise ImportError(
                    "openai package is required for evaluation. "
                    "Install with: pip install 'openai>=1.60.0'"
                ) from exc
            api_key: str = self._settings["api_key"]
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is not set. Add it to tfg.env or export "
                    "it as an environment variable before running evaluation."
                )
            self._client = openai.OpenAI(api_key=api_key)
        return self._client

    def evaluate_config_samples(
        self,
        experiment_json: dict[str, Any],
        experiment_json_path: Path,
        pending_only: bool = True,
    ) -> dict[str, Any]:

        from src.prompts import build_user_prompt, SYSTEM_PROMPT
        from src.evaluation.schemas import RAG_EVAL_BATCH_SCHEMA, SCHEMA_NAME

        config_name: str = experiment_json.get("config_name", "unknown")
        samples: list[dict[str, Any]] = experiment_json.get("samples", [])

        if not samples:
            logger.info(
                "[judge] Config '%s': no samples found, skipping.", config_name
            )
            return experiment_json


        if pending_only:
            to_eval: list[dict[str, Any]] = [
                s for s in samples
                if s.get("eval", {}).get("status") in (
                    STATUS_PENDING, STATUS_RETRY_PENDING
                )
            ]
        else:
            to_eval = list(samples)


        for s in to_eval:
            if not s.get("config_name"):
                s["config_name"] = config_name

        if not to_eval:
            logger.info(
                "[judge] Config '%s': no pending samples, skipping.", config_name
            )
            return experiment_json

        model: str = self._settings["model"]
        batch_size: int = self._settings["sync_batch_size"]


        batches: list[list[dict[str, Any]]] = [
            to_eval[i: i + batch_size]
            for i in range(0, len(to_eval), batch_size)
        ]
        total_batches: int = len(batches)

        logger.info(
            "[judge] Config '%s': evaluating %d / %d samples "
            "(%d batch%s of up to %d samples each).",
            config_name,
            len(to_eval),
            len(samples),
            total_batches,
            "es" if total_batches != 1 else "",
            batch_size,
        )


        experiment_json.setdefault("evaluation", {})["status"] = (
            "evaluation_in_progress"
        )
        experiment_json["evaluation"]["started_at"] = (
            _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        )

        sync_batches_completed: int = (
            experiment_json["evaluation"].get("sync_batches_completed", 0)
        )


        samples_evaluated_so_far: int = 0

        for batch_idx, batch in enumerate(batches):
            batch_label: str = (
                f"config {config_name} batch {batch_idx + 1}/{total_batches}"
            )
            expected_ids: list[str] = [s["eval_item_id"] for s in batch]
            batch_id: str = (
                f"sync::{config_name}::{batch_idx:03d}"
            )

            result: dict[str, Any] | None = self._call_with_retry(
                batch=batch,
                expected_ids=expected_ids,
                batch_label=batch_label,
                system_prompt=SYSTEM_PROMPT,
                user_prompt_fn=build_user_prompt,
                schema=RAG_EVAL_BATCH_SCHEMA,
                schema_name=SCHEMA_NAME,
                model=model,
            )

            if result is None:

                logger.warning(
                    "[judge] %s: all retries exhausted, marking %d samples "
                    "retry_pending.",
                    batch_label, len(batch),
                )
                now: str = _dt.datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
                for sample in batch:
                    ev: dict[str, Any] = sample.setdefault("eval", {})
                    ev["status"] = STATUS_RETRY_PENDING
                    ev["attempt_count"] = ev.get("attempt_count", 0) + 1
                    ev["last_error"] = f"All sync retries exhausted for {batch_label}"
                    ev["evaluated_at"] = now

                logger.info(
                    "[judge] Config '%s': batch %d/%d - %d/%d samples evaluated"
                    " (batch failed, samples marked retry_pending).",
                    config_name,
                    batch_idx + 1,
                    total_batches,
                    samples_evaluated_so_far,
                    len(to_eval),
                )
            else:

                results_by_id: dict[str, dict[str, Any]] = {
                    r["eval_item_id"]: r
                    for r in result["results"]
                }
                now = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                for sample in batch:
                    item_id: str = sample["eval_item_id"]
                    judge_result: dict[str, Any] = results_by_id[item_id]
                    ev = sample.setdefault("eval", {})
                    ev["status"] = STATUS_COMPLETED
                    ev["method"] = METHOD_SYNC
                    ev["model"] = model
                    ev["batch_mode"] = "sync"
                    ev["batch_id"] = batch_id
                    ev["batch_custom_id"] = None
                    ev["evaluated_at"] = now
                    ev["attempt_count"] = ev.get("attempt_count", 0) + 1
                    ev["last_error"] = None
                    ev["scores"] = {
                        "correctness": float(judge_result["correctness"]),
                        "faithfulness": float(judge_result["faithfulness"]),
                        "answer_relevance": float(
                            judge_result["answer_relevance"]
                        ),
                        "context_support": float(
                            judge_result["context_support"]
                        ),
                        "refusal_quality": float(
                            judge_result["refusal_quality"]
                        ),
                        "overall": float(judge_result["overall"]),
                    }


                    _contexts: list = sample.get("contexts") or []
                    _is_no_context: bool = (
                        config_name == "no_rag" or not _contexts
                    )


                    _raw_failure_type: str = str(
                        judge_result.get("failure_type", "uncertain")
                    )
                    if _is_no_context and _raw_failure_type != "retrieval_failure":
                        logger.debug(
                            "[judge] %s sample %s: correcting failure_type "
                            "%r → 'retrieval_failure' (no-context rule)",
                            config_name, item_id, _raw_failure_type,
                        )
                        _raw_failure_type = "retrieval_failure"

                    _raw_is_false_refusal: bool = bool(
                        judge_result.get("is_false_refusal", False)
                    )
                    if _is_no_context and _raw_is_false_refusal:
                        logger.debug(
                            "[judge] %s sample %s: correcting is_false_refusal "
                            "True → False (no-context rule)",
                            config_name, item_id,
                        )
                        _raw_is_false_refusal = False

                    _raw_context_sufficient: bool = bool(
                        judge_result.get("context_sufficient", False)
                    )
                    if _is_no_context and _raw_context_sufficient:
                        logger.debug(
                            "[judge] %s sample %s: correcting context_sufficient "
                            "True → False (no-context rule)",
                            config_name, item_id,
                        )
                        _raw_context_sufficient = False

                    _raw_answer_supported: bool = bool(
                        judge_result.get("answer_supported_by_context", False)
                    )
                    if _is_no_context and _raw_answer_supported:
                        logger.debug(
                            "[judge] %s sample %s: correcting "
                            "answer_supported_by_context True → False "
                            "(no-context rule)",
                            config_name, item_id,
                        )
                        _raw_answer_supported = False

                    ev["judge_notes"] = {

                        "answer_type": judge_result["answer_type"],
                        "is_refusal": bool(judge_result["is_refusal"]),
                        "is_correct_refusal": bool(
                            judge_result["is_correct_refusal"]
                        ),
                        "is_false_refusal": _raw_is_false_refusal,
                        "has_contradiction": bool(
                            judge_result["has_contradiction"]
                        ),


                        "answer_correct": bool(
                            judge_result.get("answer_correct", False)
                        ),
                        "context_sufficient": _raw_context_sufficient,
                        "answer_supported_by_context": _raw_answer_supported,
                        "failure_type": _raw_failure_type,
                        "judge_summary": str(
                            judge_result.get("judge_summary", "")
                        ),
                        "evidence_quotes": list(
                            judge_result.get("evidence_quotes", [])
                        ),
                    }
                    if _is_no_context:

                        ev["scores"]["faithfulness"] = 0.0
                        ev["scores"]["context_support"] = 0.0
                sync_batches_completed += 1
                samples_evaluated_so_far += len(batch)
                logger.info(
                    "[judge] Config '%s': batch %d/%d done - %d/%d samples evaluated.",
                    config_name,
                    batch_idx + 1,
                    total_batches,
                    samples_evaluated_so_far,
                    len(to_eval),
                )


            _save_experiment_json(experiment_json, experiment_json_path)


        _update_root_evaluation(
            experiment_json=experiment_json,
            model=model,
            sync_batches_completed=sync_batches_completed,
        )
        _save_experiment_json(experiment_json, experiment_json_path)

        completed: int = sum(
            1 for s in samples
            if s.get("eval", {}).get("status") == STATUS_COMPLETED
        )
        pending: int = sum(
            1 for s in samples
            if s.get("eval", {}).get("status")
            in (STATUS_PENDING, STATUS_RETRY_PENDING)
        )
        logger.info(
            "[judge] Config '%s': completed=%d pending=%d",
            config_name, completed, pending,
        )
        return experiment_json


    def _call_with_retry(
        self,
        batch: list[dict[str, Any]],
        expected_ids: list[str],
        batch_label: str,
        system_prompt: str,
        user_prompt_fn: Any,
        schema: dict[str, Any],
        schema_name: str,
        model: str,
    ) -> dict[str, Any] | None:

        max_retries: int = self._settings["max_retries"]
        base_sleep: float = self._settings["retry_base_sleep"]
        max_sleep: float = self._settings["retry_max_sleep"]

        client = self._get_client()
        user_prompt: str = user_prompt_fn(batch)

        for attempt in range(1, max_retries + 1):
            try:
                response = client.responses.create(
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": schema_name,
                            "strict": True,
                            "schema": schema,
                        }
                    },
                    temperature=0,
                    store=False,
                )
                raw_text: str = response.output_text
                parsed: dict[str, Any] = json.loads(raw_text)
                validation_error: str | None = _validate_batch_response(
                    parsed, expected_ids
                )
                if validation_error:
                    raise _ValidationError(validation_error)
                logger.debug(
                    "[judge] %s succeeded on attempt %d.", batch_label, attempt
                )
                return parsed

            except _ValidationError as exc:
                error_msg: str = f"validation error: {exc}"
                sleep_s: float = _jitter_sleep(base_sleep, attempt, max_sleep)
                logger.warning(
                    "[judge] OpenAI evaluation batch failed for %s with %s. "
                    "Retrying in %.0fs, attempt %d/%d.",
                    batch_label, error_msg, sleep_s, attempt, max_retries,
                )
                if attempt < max_retries:
                    time.sleep(sleep_s)

            except Exception as exc:
                status_code: int = getattr(
                    getattr(exc, "response", None), "status_code", 0
                ) or 0
                err_type: str = type(exc).__name__
                error_msg = f"{err_type}: {exc}"

                if not _is_retryable(exc, status_code):
                    logger.error(
                        "[judge] Non-retryable error for %s: %s",
                        batch_label, error_msg,
                    )
                    return None

                sleep_s = _jitter_sleep(base_sleep, attempt, max_sleep)
                logger.warning(
                    "[judge] OpenAI evaluation batch failed for %s with "
                    "%s (HTTP %d). Retrying in %.0fs, attempt %d/%d.",
                    batch_label,
                    error_msg,
                    status_code,
                    sleep_s,
                    attempt,
                    max_retries,
                )
                if attempt < max_retries:
                    time.sleep(sleep_s)

        logger.error(
            "[judge] %s: all %d retries exhausted.", batch_label, max_retries
        )
        return None


class _ValidationError(Exception):
    pass


def _jitter_sleep(base: float, attempt: int, max_sleep: float) -> float:

    cap: float = min(base * (2 ** (attempt - 1)), max_sleep)
    return random.uniform(0.0, cap)


def _is_retryable(exc: Exception, status_code: int) -> bool:

    if status_code in _RETRYABLE_STATUS_CODES:
        return True
    exc_type: str = type(exc).__name__.lower()
    retryable_types: tuple[str, ...] = (
        "connectionerror",
        "timeouterror",
        "timeout",
        "connecttimeout",
        "readtimeout",
        "rateLimitError",
        "apierror",
        "internalservererror",
    )
    return any(t in exc_type for t in retryable_types)


def _save_experiment_json(
    experiment_json: dict[str, Any], path: Path
) -> None:

    tmp_path: Path = path.with_suffix(".json.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(experiment_json, f, indent=2, ensure_ascii=False)
        tmp_path.replace(path)
        logger.debug("[judge] Saved %s", path.name)
    except OSError as exc:
        logger.error("[judge] Failed to save %s: %s", path, exc)
        raise


def _update_root_evaluation(
    experiment_json: dict[str, Any],
    model: str,
    sync_batches_completed: int,
) -> None:

    samples: list[dict[str, Any]] = experiment_json.get("samples", [])
    total: int = len(samples)
    evaluated: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status") == STATUS_COMPLETED
    )
    pending: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status")
        in (STATUS_PENDING, STATUS_RETRY_PENDING)
    )
    failed: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status") in (STATUS_FAILED, "error")
    )
    batch_running: int = sum(
        1 for s in samples
        if s.get("eval", {}).get("status")
        in (STATUS_BATCH_SUBMITTED, STATUS_BATCH_RUNNING)
    )

    if evaluated == total:
        status: str = STATUS_COMPLETED
    elif batch_running > 0:
        status = "evaluation_in_progress"
    elif evaluated > 0:
        status = "partial"
    else:
        status = STATUS_PENDING

    ev: dict[str, Any] = experiment_json.setdefault("evaluation", {})
    ev["status"] = status
    ev["method"] = METHOD_SYNC
    ev["model"] = model
    ev["scores_scale"] = "0_to_100"
    ev.setdefault(
        "started_at",
        _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    )
    if status == STATUS_COMPLETED:
        ev["completed_at"] = _dt.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
    ev["num_samples_total"] = total
    ev["num_samples_evaluated"] = evaluated
    ev["num_samples_pending"] = pending
    ev["num_samples_failed"] = failed
    ev["sync_batches_completed"] = sync_batches_completed
    ev.setdefault("async_batches_submitted", 0)
    ev.setdefault("async_batches_completed", 0)
    ev["last_error"] = None if (pending == 0 and failed == 0) else ev.get(
        "last_error"
    )


_BATCH_TERMINAL: frozenset[str] = frozenset({
    "completed", "failed", "expired", "cancelled"
})

METHOD_ASYNC: str = "openai_batch_api_structured_outputs"


def submit_async_batches(
    unresolved: dict[str, list[dict[str, Any]]],
    run_dir: Path,
    model: str | None = None,
) -> int:

    from src.evaluation.schemas import RAG_EVAL_BATCH_SCHEMA, SCHEMA_NAME
    from src.prompts import build_user_prompt, SYSTEM_PROMPT

    settings: dict[str, Any] = _get_settings()
    if model:
        settings["model"] = model
    client = _get_client(settings["api_key"])

    submitted: int = 0
    for config_name, items in unresolved.items():
        if not items:
            continue
        try:
            batch_id: str = _submit_one_config_batch(
                client=client,
                config_name=config_name,
                items=items,
                run_dir=run_dir,
                model=settings["model"],
                schema=RAG_EVAL_BATCH_SCHEMA,
                schema_name=SCHEMA_NAME,
                system_prompt=SYSTEM_PROMPT,
                user_prompt_fn=build_user_prompt,
            )
            if batch_id:

                _mark_samples_batch_submitted(
                    items=items,
                    batch_id=batch_id,
                    config_name=config_name,
                    run_dir=run_dir,
                    model=settings["model"],
                )
                submitted += 1
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error(
                "[batch_api] Failed to submit batch for config '%s': %s",
                config_name, exc,
            )
    return submitted


def poll_async_batches(run_dir: Path) -> dict[str, Any]:

    settings: dict[str, Any] = _get_settings()
    client = _get_client(settings["api_key"])

    artifacts_root: Path = run_dir / "evaluation_artifacts"
    if not artifacts_root.exists():
        logger.info("[batch_api] No evaluation_artifacts directory found.")
        return {"checked": 0, "completed": 0, "still_pending": 0, "failed": 0}

    checked: int = 0
    completed_total: int = 0
    still_pending: int = 0
    failed_total: int = 0

    for config_dir in sorted(artifacts_root.iterdir()):
        if not config_dir.is_dir():
            continue
        config_name: str = config_dir.name
        manifest_path: Path = config_dir / "batch_manifest.json"
        if not manifest_path.exists():
            continue

        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "[batch_api] Cannot read manifest for '%s': %s", config_name, exc
            )
            continue

        batch_id: str = manifest.get("batch_id", "")
        if not batch_id:
            continue

        checked += 1
        try:
            batch_obj = client.batches.retrieve(batch_id)
        except Exception as exc:
            logger.error(
                "[batch_api] Cannot retrieve batch '%s': %s", batch_id, exc
            )
            still_pending += 1
            continue

        batch_status: str = batch_obj.status
        manifest["last_polled_at"] = _dt.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        manifest["batch_status"] = batch_status

        if batch_status not in _BATCH_TERMINAL:
            logger.info(
                "[batch_api] Config '%s' batch '%s' status: %s (still running)",
                config_name, batch_id, batch_status,
            )
            still_pending += 1
            _save_manifest(manifest, manifest_path)
            continue

        if batch_status in ("failed", "expired", "cancelled"):
            logger.warning(
                "[batch_api] Config '%s' batch '%s' terminal status: %s",
                config_name, batch_id, batch_status,
            )
            failed_total += 1
            manifest["completed_at"] = _dt.datetime.now().strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            _save_manifest(manifest, manifest_path)
            continue


        logger.info(
            "[batch_api] Config '%s' batch '%s' completed - processing output.",
            config_name, batch_id,
        )
        try:
            n_ok, n_err = _process_batch_output(
                client=client,
                batch_obj=batch_obj,
                config_name=config_name,
                manifest=manifest,
                run_dir=run_dir,
                output_dir=config_dir,
            )
            completed_total += 1
            manifest["completed_at"] = _dt.datetime.now().strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            manifest["items_processed_ok"] = n_ok
            manifest["items_processed_err"] = n_err
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error(
                "[batch_api] Error processing output for '%s': %s",
                config_name, exc,
            )
            failed_total += 1

        _save_manifest(manifest, manifest_path)

    return {
        "checked": checked,
        "completed": completed_total,
        "still_pending": still_pending,
        "failed": failed_total,
    }


def _submit_one_config_batch(
    client: Any,
    config_name: str,
    items: list[dict[str, Any]],
    run_dir: Path,
    model: str,
    schema: dict[str, Any],
    schema_name: str,
    system_prompt: str,
    user_prompt_fn: Any,
) -> str:

    output_dir: Path = run_dir / "evaluation_artifacts" / config_name
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_lines: list[str] = []
    custom_id_to_item: dict[str, dict[str, Any]] = {}

    for item in items:
        custom_id: str = item["eval_item_id"]

        single_sample_prompt: str = user_prompt_fn([item])
        line: dict[str, Any] = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": single_sample_prompt},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    }
                },
                "temperature": 0,
                "store": False,
            },
        }
        jsonl_lines.append(json.dumps(line, ensure_ascii=False))
        custom_id_to_item[custom_id] = item

    if not jsonl_lines:
        logger.warning(
            "[batch_api] Config '%s': no items to submit.", config_name
        )
        return ""


    timestamp: str = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path: Path = output_dir / f"batch_input_{timestamp}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl_lines))

    logger.info(
        "[batch_api] Config '%s': uploading %d items from %s",
        config_name, len(jsonl_lines), jsonl_path.name,
    )

    with open(jsonl_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="batch")

    batch_obj = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={
            "run_id": items[0].get("run_id", ""),
            "config_name": config_name,
        },
    )

    batch_id: str = batch_obj.id
    logger.info(
        "[batch_api] Config '%s': batch submitted, id=%s (%d items)",
        config_name, batch_id, len(jsonl_lines),
    )


    manifest: dict[str, Any] = {
        "batch_id": batch_id,
        "config_name": config_name,
        "run_id": items[0].get("run_id", ""),
        "submitted_at": _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "last_polled_at": None,
        "batch_status": "validating",
        "completed_at": None,
        "num_items": len(jsonl_lines),
        "input_file_id": file_obj.id,
        "output_file_id": None,
        "custom_ids": list(custom_id_to_item.keys()),
        "items_processed_ok": 0,
        "items_processed_err": 0,
    }
    _save_manifest(manifest, output_dir / "batch_manifest.json")

    return batch_id


def _mark_samples_batch_submitted(
    items: list[dict[str, Any]],
    batch_id: str,
    config_name: str,
    run_dir: Path,
    model: str,
) -> None:

    if not items:
        return


    exp_path: Path = run_dir / "experiments" / f"{config_name}.json"
    if not exp_path.exists():
        logger.error(
            "[batch_api] Experiment JSON not found for config '%s': %s",
            config_name, exp_path,
        )
        return

    try:
        with open(exp_path, encoding="utf-8") as f:
            exp_json: dict[str, Any] = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(
            "[batch_api] Cannot load experiment JSON '%s': %s", exp_path, exc
        )
        return

    item_ids: set[str] = {item["eval_item_id"] for item in items}
    now: str = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for sample in exp_json.get("samples", []):
        if sample.get("eval_item_id") in item_ids:
            ev: dict[str, Any] = sample.setdefault("eval", {})
            ev["status"] = STATUS_BATCH_SUBMITTED
            ev["method"] = METHOD_ASYNC
            ev["model"] = model
            ev["batch_mode"] = "async"
            ev["batch_id"] = batch_id
            ev["evaluated_at"] = now
            ev["attempt_count"] = ev.get("attempt_count", 0) + 1


            ev["last_error"] = None
            ev["scores"] = None
            ev["judge_notes"] = None


    _update_root_evaluation(
        experiment_json=exp_json,
        model=model,
        sync_batches_completed=exp_json.get("evaluation", {}).get(
            "sync_batches_completed", 0
        ),
    )
    exp_json["evaluation"]["async_batches_submitted"] = (
        exp_json["evaluation"].get("async_batches_submitted", 0) + 1
    )

    try:
        tmp: Path = exp_path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(exp_json, f, indent=2, ensure_ascii=False)
        tmp.replace(exp_path)
    except OSError as exc:
        logger.error(
            "[batch_api] Failed to save experiment JSON '%s': %s", exp_path, exc
        )


def _process_batch_output(
    client: Any,
    batch_obj: Any,
    config_name: str,
    manifest: dict[str, Any],
    run_dir: Path,
    output_dir: Path,
) -> tuple[int, int]:

    output_file_id: str = batch_obj.output_file_id or ""
    if not output_file_id:
        raise ValueError(
            f"Batch '{batch_obj.id}' completed but output_file_id is empty."
        )

    manifest["output_file_id"] = output_file_id


    timestamp: str = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_jsonl: Path = output_dir / f"batch_output_{timestamp}.jsonl"

    content: bytes = client.files.content(output_file_id).content
    with open(output_jsonl, "wb") as f:
        f.write(content)

    logger.info(
        "[batch_api] Config '%s': saved output to %s", config_name, output_jsonl.name
    )


    results_by_custom_id: dict[str, dict[str, Any]] = {}
    errors_by_custom_id: dict[str, str] = {}

    for line in content.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue
        custom_id: str = obj.get("custom_id", "")
        if not custom_id:
            continue
        if obj.get("error"):
            errors_by_custom_id[custom_id] = str(obj["error"])
            continue

        try:
            output_text: str = obj["response"]["body"]["output_text"]
            parsed: dict[str, Any] = json.loads(output_text)

            if parsed.get("results") and len(parsed["results"]) >= 1:
                results_by_custom_id[custom_id] = parsed["results"][0]
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            errors_by_custom_id[custom_id] = str(exc)


    exp_path: Path = run_dir / "experiments" / f"{config_name}.json"
    try:
        with open(exp_path, encoding="utf-8") as f:
            exp_json: dict[str, Any] = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Cannot load experiment JSON '{exp_path}': {exc}"
        ) from exc

    now: str = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    model: str = manifest.get("model", exp_json.get("evaluation", {}).get("model", ""))
    n_ok: int = 0
    n_err: int = 0

    for sample in exp_json.get("samples", []):
        custom_id = sample.get("eval_item_id", "")
        if custom_id in results_by_custom_id:
            judge_result: dict[str, Any] = results_by_custom_id[custom_id]
            ev: dict[str, Any] = sample.setdefault("eval", {})
            ev["status"] = STATUS_COMPLETED
            ev["method"] = METHOD_ASYNC
            ev["model"] = model
            ev["batch_mode"] = "async"
            ev["batch_id"] = manifest.get("batch_id", "")
            ev["batch_custom_id"] = custom_id
            ev["evaluated_at"] = now
            ev["last_error"] = None
            ev["scores"] = {
                "correctness": float(judge_result.get("correctness", 0.0)),
                "faithfulness": float(judge_result.get("faithfulness", 0.0)),
                "answer_relevance": float(
                    judge_result.get("answer_relevance", 0.0)
                ),
                "context_support": float(
                    judge_result.get("context_support", 0.0)
                ),
                "refusal_quality": float(
                    judge_result.get("refusal_quality", 0.0)
                ),
                "overall": float(judge_result.get("overall", 0.0)),
            }
            ev["judge_notes"] = {

                "answer_type": judge_result.get("answer_type", "unknown"),
                "is_refusal": bool(judge_result.get("is_refusal", False)),
                "is_correct_refusal": bool(
                    judge_result.get("is_correct_refusal", False)
                ),
                "is_false_refusal": bool(
                    judge_result.get("is_false_refusal", False)
                ),
                "has_contradiction": bool(
                    judge_result.get("has_contradiction", False)
                ),


                "answer_correct": bool(
                    judge_result.get("answer_correct", False)
                ),
                "context_sufficient": bool(
                    judge_result.get("context_sufficient", False)
                ),
                "answer_supported_by_context": bool(
                    judge_result.get("answer_supported_by_context", False)
                ),
                "failure_type": str(
                    judge_result.get("failure_type", "uncertain")
                ),
                "judge_summary": str(
                    judge_result.get("judge_summary", "")
                ),
                "evidence_quotes": list(
                    judge_result.get("evidence_quotes", [])
                ),
            }
            n_ok += 1
        elif custom_id in errors_by_custom_id:
            ev = sample.setdefault("eval", {})
            ev["status"] = STATUS_RETRY_PENDING
            ev["last_error"] = errors_by_custom_id[custom_id]
            n_err += 1


    recompute_llm_eval_metrics(exp_json)
    _update_root_evaluation(
        experiment_json=exp_json,
        model=model,
        sync_batches_completed=exp_json.get("evaluation", {}).get(
            "sync_batches_completed", 0
        ),
    )

    tmp: Path = exp_path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(exp_json, f, indent=2, ensure_ascii=False)
    tmp.replace(exp_path)

    logger.info(
        "[batch_api] Config '%s': %d ok, %d errors", config_name, n_ok, n_err
    )
    return n_ok, n_err


def _save_manifest(manifest: dict[str, Any], path: Path) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _get_settings() -> dict[str, Any]:

    try:
        from src.config_loader import get_config
        return {
            "api_key": get_config("OPENAI_API_KEY", ""),
            "model": get_config("OPENAI_EVAL_MODEL", "gpt-5.4-mini"),
            "poll_interval": int(
                get_config("OPENAI_EVAL_ASYNC_POLL_SECONDS", "60")
            ),
            "timeout": int(
                get_config("OPENAI_EVAL_ASYNC_TIMEOUT_SECONDS", "86400")
            ),
        }
    except ImportError:
        return {
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "model": os.environ.get("OPENAI_EVAL_MODEL", "gpt-5.4-mini"),
            "poll_interval": int(
                os.environ.get("OPENAI_EVAL_ASYNC_POLL_SECONDS", "60")
            ),
            "timeout": int(
                os.environ.get("OPENAI_EVAL_ASYNC_TIMEOUT_SECONDS", "86400")
            ),
        }


def _get_client(api_key: str) -> Any:

    try:
        import openai
    except ImportError as exc:
        raise ImportError(
            "openai package is required for evaluation. "
            "Install with: pip install 'openai>=1.60.0'"
        ) from exc
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to tfg.env or export it as "
            "an environment variable before running batch evaluation."
        )
    return openai.OpenAI(api_key=api_key)


__all__: list[str] = [
    "DEFAULT_LOG_DIR",
    "SCHEMA_VERSION_V2",
    "PerformanceTimer",
    "ExperimentLogV2",
    "ExperimentRunner",
    "RunManifest",
    "append_to_run_index",
    "create_run_id",
    "format_duration",
    "generate_summary_v2",
    "initial_pending_evaluation_metadata",
    "initial_pending_sample_eval",
    "make_eval_item_id",

    "evaluate_run",
    "collect_unresolved_eval_items",
    "regenerate_summary_for_run",
    "OpenAIRagJudge",
    "recompute_llm_eval_metrics",
    "recompute_llm_eval_metrics",
    "OpenAIRagJudge",
    "STATUS_COMPLETED",
    "STATUS_PENDING",
    "STATUS_RETRY_PENDING",
    "STATUS_FAILED",
    "STATUS_BATCH_SUBMITTED",
    "STATUS_BATCH_RUNNING",
    "METHOD_SYNC",
    "submit_async_batches",
    "poll_async_batches",
]
