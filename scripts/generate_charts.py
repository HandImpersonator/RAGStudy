from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from scripts.thesis_artifacts import (
    FAMILY_MAIN_EXPERIMENT,
    FAMILY_MODEL_SELECTION,
    FAMILY_COMBO_SWEEP,
    EXPERIMENT_ORDER,
    safe_label as _safe_label,
    latex_escape as _latex_escape,
    write_budget_macros,
    write_budget_table,
    write_group_thesis_artifacts,
    write_cross_model_thesis_artifacts,
)
from scripts.compare_component_effects import (
    main as _run_component_effects_analysis,
)
from scripts.run_retriever_comparison import main as _run_retriever_comparison

warnings.filterwarnings("ignore", message=".*Tight layout.*", category=UserWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
LOG_DIR: Path = _PROJECT_ROOT / "logs"
OUTPUT_DIR: Path = _PROJECT_ROOT / "output" / "thesis"


EXPERIMENT_LABELS: dict[str, str] = {
    "no_rag":                    r"Sin \acro{RAG}",

    "baseline_k":                r"\acro{Baseline} \acro{BM25}",
    "baseline_s":                r"\acro{Baseline} \acro{FAISS}",
    "baseline_k_rr":             r"\acro{Baseline} \acro{BM25}+\acro{RR}",
    "baseline_s_rr":             r"\acro{Baseline} \acro{FAISS}+\acro{RR}",

    "baseline_k_grounded":       r"\acro{Baseline} \acro{BM25}+\acro{G}",
    "baseline_s_grounded":       r"\acro{Baseline} \acro{FAISS}+\acro{G}",
    "baseline_k_rr_grounded":    r"\acro{Baseline} \acro{BM25}+\acro{RR}+\acro{G}",
    "baseline_s_rr_grounded":    r"\acro{Baseline} \acro{FAISS}+\acro{RR}+\acro{G}",

    "optimized_k":               r"\abbr{Optim}{Optim.} \acro{BM25}",
    "optimized_s":               r"\abbr{Optim}{Optim.} \acro{FAISS}",
    "optimized_k_rr":            r"\abbr{Optim}{Optim.} \acro{BM25}+\acro{RR}",
    "optimized_s_rr":            r"\abbr{Optim}{Optim.} \acro{FAISS}+\acro{RR}",

    "optimized_k_grounded":      r"\abbr{Optim}{Optim.} \acro{BM25}+\acro{G}",
    "optimized_s_grounded":      r"\abbr{Optim}{Optim.} \acro{FAISS}+\acro{G}",
    "optimized_k_rr_grounded":   r"\abbr{Optim}{Optim.} \acro{BM25}+\acro{RR}+\acro{G}",
    "optimized_s_rr_grounded":   r"\abbr{Optim}{Optim.} \acro{FAISS}+\acro{RR}+\acro{G}",
}
EXPERIMENT_LABELS_GRAPH: dict[str, str] = {
    "no_rag":                    r"Sin RAG",

    "baseline_k":                r"Baseline BM25",
    "baseline_s":                r"Baseline FAISS",
    "baseline_k_rr":             r"Baseline BM25+RR",
    "baseline_s_rr":             r"Baseline FAISS+RR",

    "baseline_k_grounded":       r"Baseline BM25+G",
    "baseline_s_grounded":       r"Baseline FAISS+G",
    "baseline_k_rr_grounded":    r"Baseline BM25+RR+G",
    "baseline_s_rr_grounded":    r"Baseline FAISS+RR+G",

    "optimized_k":               r"Optim. BM25",
    "optimized_s":               r"Optim. FAISS",
    "optimized_k_rr":            r"Optim. BM25+RR",
    "optimized_s_rr":            r"Optim. FAISS+RR",

    "optimized_k_grounded":      r"Optim. BM25+G",
    "optimized_s_grounded":      r"Optim. FAISS+G",
    "optimized_k_rr_grounded":   r"Optim. BM25+RR+G",
    "optimized_s_rr_grounded":   r"Optim. FAISS+RR+G",
}


EXPERIMENT_COLORS: dict[str, str] = {
    "no_rag":                    "#E74C3C",

    "baseline_k":                "#3498DB",
    "baseline_s":                "#2980B9",
    "baseline_k_rr":             "#1ABC9C",
    "baseline_s_rr":             "#16A085",

    "baseline_k_grounded":       "#48C9B0",
    "baseline_s_grounded":       "#1A8A74",
    "baseline_k_rr_grounded":    "#0E6655",
    "baseline_s_rr_grounded":    "#0A4D3A",

    "optimized_k":               "#F39C12",
    "optimized_s":               "#E67E22",
    "optimized_k_rr":            "#D35400",
    "optimized_s_rr":            "#A04000",

    "optimized_k_grounded":      "#C0392B",
    "optimized_s_grounded":      "#922B21",
    "optimized_k_rr_grounded":   "#784212",
    "optimized_s_rr_grounded":   "#4A235A",
}


QUALITY_METRICS: list[tuple[str, str]] = [
    ("correctness_mean",       "Corrección"),
    ("faithfulness_mean",      "Faithfulness medio"),
    ("answer_relevance_mean",  "Relevancia de la respuesta"),
    ("context_support_mean",   "Soporte Contexto"),
    ("overall_mean",           "Puntuación Global"),
]


RATE_METRICS: list[tuple[str, str]] = [
    ("answer_accuracy",          "Resp. Correcta"),
    ("context_sufficiency_rate", "Contexto Suf."),
    ("faithfulness_rate",        "Tasa de fidelidad al contexto"),
    ("contradiction_rate",       "Contradicción"),
    ("overconfidence_rate",      "Alucinación (< mejor)"),
]


FAILURE_METRICS: list[tuple[str, str]] = [
    ("retrieval_failure_rate",  "Fallo Retrieval"),
    ("generation_failure_rate", "Fallo Generación"),
    ("combined_failure_rate",   "Fallo Combinado"),
    ("uncertain_rate",          "Incierto"),
]


FAILURE_COLORS: dict[str, str] = {
    "retrieval_failure_rate":  "#E74C3C",
    "generation_failure_rate": "#F39C12",
    "combined_failure_rate":   "#8E44AD",
    "uncertain_rate":          "#95A5A6",
}

CHART_SUPPORTED_FAMILIES: list[str] = [
    FAMILY_MAIN_EXPERIMENT,
    FAMILY_MODEL_SELECTION,
]

DEFAULT_INCLUDED_FAMILIES: list[str] = [FAMILY_MAIN_EXPERIMENT]


FAMILY_OTHER: str = "other"


def _dfmt(value: float, decimals: int = 2) -> str:

    return f"{value:.{decimals}f}".replace(".", ",")


def _es_yformatter(x: float, _pos: int) -> str:

    if x == int(x):
        return str(int(x))
    return f"{x:.1f}".replace(".", ",")


def _es_func_formatter() -> Any:

    import matplotlib.ticker as mticker
    return mticker.FuncFormatter(_es_yformatter)


def _stagger_bar_label_heights(
    bars: Any,
    values: list[float],
    ax: Any,
    fmt_fn: Any,
    base_offset: float = 1.5,
    stagger_step: float = 2.5,
    bar_index: int = 0,
    min_val: float = 0.5,
    fontsize: int = 10,
    suffix: str = "",
    rotation: float = 0,
) -> None:


    vert_offset: float = base_offset + (bar_index % 2) * stagger_step


    ha: str = "left" if rotation != 0 else "center"
    for bar, val in zip(bars, values):
        if val > min_val:


            label_y: float = max(bar.get_height(), 0.0) + vert_offset
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                label_y,
                fmt_fn(val) + suffix,
                ha=ha, va="bottom",
                fontsize=fontsize, fontweight="bold",
                rotation=rotation,
                rotation_mode="anchor",
            )


def discover_summaries(
    log_dir: Path,
    include_families: list[str] | None = None,
) -> list[dict[str, Any]]:

    summaries: list[dict[str, Any]] = []


    filtered_out_families: dict[str, int] = {}
    total_v2_seen: int = 0

    def _try_load(path: Path) -> dict[str, Any] | None:
        nonlocal total_v2_seen
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            if data.get("schema_version") != "2.0":
                logger.debug("Skipping non-v2.0 summary: %s", path.name)
                return None
            if data.get("report_type") != "experiment_summary":
                return None
            total_v2_seen += 1
            data["_source_file"] = str(path)
            family = _infer_experiment_family(data, log_dir)
            data["_experiment_family"] = family

            if include_families is not None and family not in include_families:
                filtered_out_families[family] = filtered_out_families.get(family, 0) + 1
                logger.debug(
                    "Skipping summary from family '%s': %s",
                    family,
                    path.name,
                )
                return None
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("No se pudo cargar %s: %s", path.name, exc)
            return None


    summaries_dir: Path = log_dir / "summaries"
    if summaries_dir.exists():
        for path in sorted(summaries_dir.glob("*experiment_summary*.json")):

            if path.suffix != ".json":
                continue
            d = _try_load(path)
            if d is not None:
                summaries.append(d)
                logger.debug("Resumen v2.0 cargado (summaries/): %s", path.name)


    for path in sorted(log_dir.glob("experiment_summary_*.json")):
        d = _try_load(path)
        if d is not None:

            existing_run_ids: set[str] = {s.get("run_id", "") for s in summaries}
            if d.get("run_id", "") not in existing_run_ids:
                summaries.append(d)
                logger.debug("Resumen v2.0 cargado (legacy): %s", path.name)


    runs_dir: Path = log_dir / "runs"
    if runs_dir.exists():
        existing_run_ids: set[str] = {s.get("run_id", "") for s in summaries}

        for path in sorted(runs_dir.glob("*/summaries/experiment_summary.json")):
            d = _try_load(path)
            if d is not None and d.get("run_id", "") not in existing_run_ids:
                summaries.append(d)
                existing_run_ids.add(d.get("run_id", ""))
                logger.debug("Resumen v2.0 cargado (runs/): %s", path)

    if not summaries:
        if total_v2_seen > 0 and filtered_out_families:


            families_str: str = ", ".join(
                f"{fam} ({count})" for fam, count in sorted(filtered_out_families.items())
            )
            included_str: str = (
                ", ".join(include_families) if include_families else "(none)"
            )
            raise FileNotFoundError(
                f"Se encontraron {total_v2_seen} resmenes v2.0 en {log_dir}, "
                f"pero todos pertenecen a familias excluidas por el filtro actual "
                f"(incluidas: [{included_str}]). Familias disponibles: {families_str}. "
                f"Aade --include-family <familia> o usa --all-families."
            )
        raise FileNotFoundError(
            f"No se encontraron resmenes con schema_version='2.0' en {log_dir}. "
            "Asegrate de haber ejecutado run_experiments.py con la versión actual. "
            "Los logs del evaluador heurstico antiguo no son compatibles."
        )

    logger.info("Resmenes v2.0 encontrados: %d", len(summaries))
    return summaries


def _summary_timestamp(summary: dict[str, Any]) -> str:

    for key in (
        "timestamp_end",
        "timestamp_start",
        "updated_at",
        "created_at",
        "timestamp",
    ):
        value = str(summary.get(key, "") or "").strip()
        if value:
            return value


    run_id = str(summary.get("run_id", "") or "")
    parts = run_id.split("_")
    if len(parts) >= 3 and parts[0] == "run":
        return f"{parts[1]}_{parts[2]}"

    return ""


def _infer_dataset(summary: dict[str, Any]) -> str:

    if "dataset" in summary:
        return str(summary["dataset"])
    return "unknown"


def _infer_model(summary: dict[str, Any]) -> str:

    detected: str = str(summary.get("model_detected", "") or "").strip()
    if detected:
        return detected.replace(":", "-").replace("/", "-")

    label: str = str(summary.get("model_label", "") or "").strip()
    if not label or label == "unknown":
        return "unknown"


    known_combo_markers: tuple[str, ...] = (
        "__bge-base__",
        "__multi-qa-mini__",
    )
    for marker in known_combo_markers:
        if marker in label:
            label = label.split(marker, 1)[0]
            break

    return label.replace(":", "-").replace("/", "-") or "unknown"


def group_summaries(
        summaries: list[dict[str, Any]],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for s in summaries:
        family: str = str(
            s.get("_experiment_family")
            or s.get("experiment_family")
            or FAMILY_MAIN_EXPERIMENT
        )
        dataset: str = _infer_dataset(s)
        model: str = _infer_model(s)
        groups[(family, dataset, model)].append(s)

    for key in groups:
        groups[key].sort(key=_summary_timestamp)

    return dict(groups)


def merge_group_summaries(
    summaries: list[dict[str, Any]],
    strategy: str = "latest",
) -> dict[str, dict[str, float]]:

    if strategy == "latest":

        source: dict[str, Any] = summaries[-1]
        result: dict[str, dict[str, float]] = {}
        for exp_name, exp_data in source.get("experiments", {}).items():
            status: str = exp_data.get("status", "")
            if status not in ("completed", "partial"):
                continue

            merged: dict[str, float] = {}
            merged.update(exp_data.get("performance_metrics", {}))
            merged.update(exp_data.get("quality_metrics", {}))

            if not merged:
                merged = dict(exp_data.get("metrics", {}))
            result[exp_name] = merged
        return result


    accumulated: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for s in summaries:
        for exp_name, exp_data in s.get("experiments", {}).items():
            status = exp_data.get("status", "")
            if status not in ("completed", "partial"):
                continue

            merged = {}
            merged.update(exp_data.get("performance_metrics", {}))
            merged.update(exp_data.get("quality_metrics", {}))
            if not merged:
                merged = dict(exp_data.get("metrics", {}))
            for metric_name, value in merged.items():
                if isinstance(value, (int, float)):
                    accumulated[exp_name][metric_name].append(float(value))

    averaged: dict[str, dict[str, float]] = {}
    for exp_name, metric_dict in accumulated.items():
        averaged[exp_name] = {
            m: sum(vals) / len(vals)
            for m, vals in metric_dict.items()
            if vals
        }
    return averaged


def _ordered_experiments(metrics: dict[str, dict[str, float]]) -> list[str]:

    present: set[str] = set(metrics.keys())
    ordered: list[str] = [e for e in EXPERIMENT_ORDER if e in present]
    for e in metrics:
        if e not in ordered:
            ordered.append(e)
    return ordered


def _summary_run_dir(summary: dict[str, Any], log_dir: Path) -> Path | None:

    run_id: str = str(summary.get("run_id", "") or "").strip()
    if not run_id:
        return None
    direct: Path = log_dir / "runs" / run_id
    if direct.exists():
        return direct


    source_file: str = str(summary.get("_source_file", "") or "")
    if source_file:
        path = Path(source_file)
        if path.name == "experiment_summary.json":
            return path.parent.parent
    return None
def _infer_experiment_family(summary: dict[str, Any], log_dir: Path) -> str:

    model_label: str = str(summary.get("model_label", "") or "")
    combo_markers: tuple[str, ...] = (
        "__bge-base__",
        "__multi-qa-mini__",
    )


    if any(marker in model_label for marker in combo_markers):
        return FAMILY_COMBO_SWEEP


    explicit: str = str(summary.get("experiment_family", "") or "").strip()
    if explicit and explicit != FAMILY_MAIN_EXPERIMENT:
        return explicit

    run_dir: Path | None = _summary_run_dir(summary, log_dir)
    if run_dir is not None:
        metadata_path: Path = run_dir / "artifact_metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                family: str = str(metadata.get("experiment_family", "") or "").strip()
                if family:
                    return family
            except (OSError, json.JSONDecodeError):
                pass
        manifest_path: Path = run_dir / "run_manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                family = str(manifest.get("experiment_family", "") or "").strip()
                if family:
                    return family


                run_type_map: dict[str, str] = {
                    "main_experiment": FAMILY_MAIN_EXPERIMENT,
                    "model_selection": FAMILY_MODEL_SELECTION,
                }
                run_type_raw: str = str(
                    manifest.get("run_type", "") or ""
                ).strip()
                if run_type_raw in run_type_map:
                    return run_type_map[run_type_raw]
            except (OSError, json.JSONDecodeError):
                pass


    if explicit:
        return explicit

    return FAMILY_MAIN_EXPERIMENT


def _infer_experiment_family_for_display(
    summary: dict[str, Any],
    log_dir: Path,
) -> str:


    model_label: str = str(summary.get("model_label", "") or "")
    combo_markers: tuple[str, ...] = (
        "__bge-base__",
        "__multi-qa-mini__",
    )
    if any(marker in model_label for marker in combo_markers):
        return FAMILY_COMBO_SWEEP

    explicit: str = str(summary.get("experiment_family", "") or "").strip()
    if explicit and explicit != FAMILY_MAIN_EXPERIMENT:
        return explicit

    run_dir: Path | None = _summary_run_dir(summary, log_dir)
    if run_dir is not None:
        metadata_path: Path = run_dir / "artifact_metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                family: str = str(
                    metadata.get("experiment_family", "") or ""
                ).strip()
                if family:
                    return family
            except (OSError, json.JSONDecodeError):
                pass

        manifest_path: Path = run_dir / "run_manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                family = str(
                    manifest.get("experiment_family", "") or ""
                ).strip()
                if family:
                    return family

                run_type_map: dict[str, str] = {
                    "main_experiment": FAMILY_MAIN_EXPERIMENT,
                    "model_selection": FAMILY_MODEL_SELECTION,
                }
                run_type_raw: str = str(
                    manifest.get("run_type", "") or ""
                ).strip()
                if run_type_raw in run_type_map:
                    return run_type_map[run_type_raw]
            except (OSError, json.JSONDecodeError):
                pass


    if explicit:
        return explicit


    return FAMILY_OTHER


def generate_quality_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)

    exp_names: list[str] = _ordered_experiments(metrics)


    active_metrics: list[tuple[str, str]] = [
        (mk, label)
        for mk, label in QUALITY_METRICS
        if mk != "overall_mean"
        and any(metrics[e].get(mk, 0.0) > 0.0 for e in exp_names)
    ]
    if any(metrics[e].get("overconfidence_rate", 0.0) > 0.0 for e in exp_names):
        active_metrics.append(("overconfidence_rate", "Alucinación (%) (< mejor)"))

    if not active_metrics:
        logger.warning("Sin métricas de calidad disponibles, omitiendo quality_comparison")
        output_path: Path = output_dir / "quality_comparison.png"
        return output_path

    n_metrics: int = len(active_metrics)
    n_exp: int = len(exp_names)
    x: Any = np.arange(n_metrics)
    width: float = min(0.7 / n_exp, 0.20)


    fig_w: float = max(12.0, n_metrics * 2.8 + n_exp * 0.5)
    fig, ax = plt.subplots(figsize=(fig_w, 7))

    for i, exp_name in enumerate(exp_names):
        values: list[float] = [
            metrics[exp_name].get(mk, 0.0) for mk, _ in active_metrics
        ]
        offset: float = (i - (n_exp - 1) / 2.0) * width
        bars = ax.bar(
            x + offset, values, width,
            label=EXPERIMENT_LABELS_GRAPH.get(exp_name, exp_name),
            color=EXPERIMENT_COLORS.get(exp_name, "#999999"),
            edgecolor="white",
            linewidth=0.5,
        )


        _stagger_bar_label_heights(
            bars, values, ax,
            fmt_fn=lambda v: _dfmt(v, 2),
            base_offset=1.0,
            stagger_step=1.5,
            bar_index=i,
            min_val=-1,
            fontsize=10,
            rotation=60,
        )

    ax.set_ylabel("Puntuación (0-100) / Tasa (0-100) %", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    title: str = r"Comparativa de Métricas de Calidad RAG (OpenAI LLM Judge)"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in active_metrics], fontsize=12)
    ax.set_ylim(0, 145)
    ax.legend(loc="upper right", fontsize=12, ncol=max(1, n_exp // 4))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    output_path = output_dir / "quality_comparison.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  quality_comparison.png → %s", output_path)
    return output_path


def generate_latency_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)

    exp_names: list[str] = _ordered_experiments(metrics)
    labels: list[str] = [EXPERIMENT_LABELS_GRAPH.get(e, e) for e in exp_names]


    query_embed_vals: list[float] = [
        metrics[e].get("query_embedding_time_mean_ms", 0.0) for e in exp_names
    ]
    retrieval_vals: list[float] = [
        metrics[e].get("retrieval_time_mean_ms", 0.0) for e in exp_names
    ]
    reranking_vals: list[float] = [
        metrics[e].get("reranking_time_mean_ms", 0.0) for e in exp_names
    ]
    ctx_sel_vals: list[float] = [
        metrics[e].get("context_selection_time_mean_ms", 0.0) for e in exp_names
    ]
    prompt_build_vals: list[float] = [
        metrics[e].get("prompt_build_time_mean_ms", 0.0) for e in exp_names
    ]
    generation_vals: list[float] = [
        metrics[e].get("generation_time_mean_ms", 0.0) for e in exp_names
    ]


    any_granular: bool = any(
        v > 0.0
        for vals in (query_embed_vals, retrieval_vals, generation_vals, prompt_build_vals)
        for v in vals
    )
    if not any_granular:
        generation_vals = [
            metrics[e].get("latency_mean_ms", 0.0) for e in exp_names
        ]


    x: Any = np.arange(len(exp_names))
    bar_width: float = 0.55
    fig, ax = plt.subplots(figsize=(max(8.0, len(exp_names) * 1.4), 6))


    ax.bar(
        x, query_embed_vals, bar_width,
        label="Embedding consulta", color="#2ECC71", edgecolor="white",
    )
    bottom_ann: list[float] = list(query_embed_vals)


    ax.bar(
        x, retrieval_vals, bar_width,
        bottom=bottom_ann,
        label="Recuperación ANN", color="#3498DB", edgecolor="white",
    )
    bottom_rerank: list[float] = [b + r for b, r in zip(bottom_ann, retrieval_vals)]


    ax.bar(
        x, reranking_vals, bar_width,
        bottom=bottom_rerank,
        label="Reranking", color="#9B59B6", edgecolor="white",
    )
    bottom_ctx: list[float] = [b + r for b, r in zip(bottom_rerank, reranking_vals)]


    ax.bar(
        x, ctx_sel_vals, bar_width,
        bottom=bottom_ctx,
        label="Selección de contexto", color="#628888", edgecolor="white",
    )
    bottom_prompt: list[float] = [b + c for b, c in zip(bottom_ctx, ctx_sel_vals)]


    ax.bar(
        x, prompt_build_vals, bar_width,
        bottom=bottom_prompt,
        label="Construcción de prompt", color="#1ABC9C", edgecolor="white",
    )
    bottom_gen: list[float] = [b + p for b, p in zip(bottom_prompt, prompt_build_vals)]


    ax.bar(
        x, generation_vals, bar_width,
        bottom=bottom_gen,
        label="Generación (LLM)", color="#E67E22", edgecolor="white",
    )


    for i, (bg, gv) in enumerate(zip(bottom_gen, generation_vals)):
        total: float = bg + gv
        if total > 0.5:
            ax.text(
                x[i], total + 5,
                f"{total:.0f} ms",
                ha="center", va="bottom",
                fontsize=10, fontweight="bold",
            )

    ax.set_ylabel("Latencia media (ms)", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    title: str = "Desglose de Latencia por Configuración"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=10)

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        fontsize=10,
        borderaxespad=0,
    )
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    output_path: Path = output_dir / "latency_breakdown.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  latency_breakdown.png → %s", output_path)
    return output_path


def generate_radar_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)

    exp_names: list[str] = _ordered_experiments(metrics)
    output_path: Path = output_dir / "radar_chart.png"

    if len(exp_names) < 2:
        logger.warning("Se necesitan al menos 2 experimentos para el radar, omitiendo")
        return output_path


    radar_dims: list[tuple[str, str, bool]] = [
        ("faithfulness_mean",      "Faithfulness",              False),
        ("answer_relevance_mean",  "Relevancia resp.",          False),
        ("context_support_mean",   "Soporte Ctx.",              False),
        ("correctness_mean",       "Corrección",                False),
        ("overconfidence_rate",    "Alucinación\n(< mejor)",    False),
        ("contradiction_rate",     "Contradicción\n(< mejor)",  False),
        ("latency_mean_ms",        "Velocidad",                 True),
    ]


    metric_raw: dict[str, list[float]] = {
        mk: [metrics[e].get(mk, 0.0) for e in exp_names]
        for mk, _, _ in radar_dims
    }

    def _normalize(
        vals: list[float],
        invert: bool,
    ) -> list[float]:

        min_v = min(vals)
        max_v = max(vals)
        clamped = list(vals)
        if max_v == min_v:
            return [0.5] * len(vals)
        normed: list[float] = [(v - min_v) / (max_v - min_v) for v in clamped]
        return [1.0 - n for n in normed] if invert else normed


    num_vars: int = len(radar_dims)
    angles: list[float] = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})

    for exp_idx, exp_name in enumerate(exp_names):
        vals_norm: list[float] = []
        for mk, _, invert in radar_dims:
            all_vals: list[float] = metric_raw[mk]
            normed: list[float] = _normalize(all_vals, invert)
            vals_norm.append(normed[exp_idx])
        vals_norm += vals_norm[:1]

        color: str = EXPERIMENT_COLORS.get(exp_name, "#999999")
        label: str = EXPERIMENT_LABELS_GRAPH.get(exp_name, exp_name)
        ax.plot(angles, vals_norm, "o-", linewidth=2, label=label, color=color)
        ax.fill(angles, vals_norm, alpha=0.12, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([label for _, label, _ in radar_dims], fontsize=12)


    ax.tick_params(axis="x", pad=20)
    ax.set_ylim(0, 1.2)
    title: str = r"Comparativa Multidimensional de Configuraciones RAG"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=15, fontweight="bold", y=1.12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.40, 1.12), fontsize=10)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  radar_chart.png → %s", output_path)
    return output_path


def generate_latex_table(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    dataset: str = "",
    model: str = "",
    family: str = "",
) -> Path:

    output_dir.mkdir(parents=True, exist_ok=True)

    exp_names: list[str] = _ordered_experiments(metrics)


    columns: list[tuple[str, str]] = [
        ("correctness_mean",       r"\abbr{Correct}{Correct.\textsuperscript{c}}"),
        ("faithfulness_mean",      r"\abbr{Faith}{Faith.\textsuperscript{c}}"),
        ("answer_relevance_mean",  r"\abbr{AnsRel}{AnsRel.\textsuperscript{c}}"),
        ("context_support_mean",   r"Soporte"),
        ("overall_mean",           r"\abbr{Global}{Global\textsuperscript{c}}"),
        ("answer_accuracy",        r"\abbr{Acc}{Acc. \%}"),
        ("context_sufficiency_rate", r"\abbr{CtxSuf}{Ctx.Suf. \%}"),
        ("contradiction_rate",       r"\abbr{Contr}{Contr. \%}"),
        ("generation_failure_rate", r"\abbr{GenFail}{GenFail. \%}"),
        ("retrieval_failure_rate",  r"\abbr{RetFail}{RetFail. \%}"),
        ("latency_mean_ms",        r"\abbr{Lat}{Lat. (ms)}"),
    ]

    col_header: str = " & ".join(
        ["Configuración"] + [label for _, label in columns]
    )
    col_format: str = "l" + "r" * len(columns)

    caption_detail: str = ""
    if dataset or model:
        parts: list[str] = []
        if dataset:
            parts.append(f"dataset: {_latex_escape(dataset)}")
        if model:
            parts.append(f"modelo: {_latex_escape(model)}")
        caption_detail = " (" + ", ".join(parts) + ")"

    caption_text = r"Resultados experimentales por configuración \acro{RAG}" + f"{caption_detail}"

    table_label: str = (
        f"tab:{_safe_label(family)}_results_"
        f"{_safe_label(dataset)}_{_safe_label(model)}"
    )

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

    for exp_name in exp_names:
        exp_metrics: dict[str, float] = metrics[exp_name]
        label: str = EXPERIMENT_LABELS.get(exp_name, exp_name)
        row_vals: list[str] = []
        for mk, _ in columns:
            val: float = exp_metrics.get(mk, 0.0)
            row_vals.append(f"{val:.0f}" if "ms" in mk else _dfmt(val, 2))
        row: str = " & ".join([label] + row_vals) + " \\\\"
        lines.append(f"    {row}")

    lines += [
        "    \\bottomrule",
        "  \\end{tabular}%",
        "  }",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        "\\end{table}",
    ]

    output_path: Path = output_dir / "comparison_table.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info("  comparison_table.tex → %s", output_path)
    return output_path


def generate_improvement_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    baseline_config: str = "no_rag",
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "improvement_chart.png"

    if baseline_config not in metrics:
        logger.warning(
            "Configuración de referencia '%s' no disponible, omitiendo improvement_chart",
            baseline_config,
        )
        return output_path

    primary_metric: str = "faithfulness_mean"
    baseline_val: float = metrics[baseline_config].get(primary_metric, 0.0)

    if baseline_val == 0.0:
        logger.warning(
            "Valor base de '%s' es 0.0, no se puede calcular mejora relativa",
            primary_metric,
        )
        return output_path

    other_configs: list[str] = [
        e for e in _ordered_experiments(metrics) if e != baseline_config
    ]

    improvements: list[float] = []
    labels: list[str] = []
    colors: list[str] = []
    for exp_name in other_configs:
        val: float = metrics[exp_name].get(primary_metric, 0.0)
        improvement_pct: float = ((val - baseline_val) / baseline_val) * 100.0
        improvements.append(improvement_pct)
        labels.append(EXPERIMENT_LABELS_GRAPH.get(exp_name, exp_name))
        colors.append(EXPERIMENT_COLORS.get(exp_name, "#999999"))

    if not improvements:
        return output_path

    y: Any = np.arange(len(other_configs))

    fig, ax = plt.subplots(figsize=(9, max(4.0, len(other_configs) * 0.9)))
    bars = ax.barh(y, improvements, color=colors, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, improvements):
        sign: str = "+" if val >= 0 else ""
        ax.text(
            bar.get_width() + (0.5 if val >= 0 else -0.5),
            bar.get_y() + bar.get_height() / 2.0,
            f"{sign}{_dfmt(val, 2)}%",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=10,
        )

    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Mejora relativa en Faithfulness (%)", fontsize=12)
    baseline_label: str = EXPERIMENT_LABELS.get(baseline_config, baseline_config)
    title: str = f"Mejora respecto a {baseline_label}"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  improvement_chart.png → %s", output_path)
    return output_path


def generate_failure_type_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "failure_type_breakdown.png"

    exp_names: list[str] = _ordered_experiments(metrics)
    labels: list[str] = [EXPERIMENT_LABELS_GRAPH.get(e, e) for e in exp_names]


    has_data: bool = any(
        metrics[e].get("retrieval_failure_rate", 0.0) > 0
        or metrics[e].get("generation_failure_rate", 0.0) > 0
        for e in exp_names
    )

    x: Any = np.arange(len(exp_names))
    bar_width: float = 0.55

    fig, ax = plt.subplots(figsize=(max(11.0, len(exp_names) * 1.6), 7))

    bottom: list[float] = [0.0] * len(exp_names)
    for metric_key, metric_label in FAILURE_METRICS:
        vals: list[float] = [
            metrics[e].get(metric_key, 0.0) for e in exp_names
        ]
        color: str = FAILURE_COLORS.get(metric_key, "#999999")
        ax.bar(
            x, vals, bar_width,
            bottom=bottom,
            label=metric_label,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        bottom = [b + v for b, v in zip(bottom, vals)]


    max_val: float = max(bottom) if bottom else 0.0
    offset_above: float = max(1.0, max_val * 0.015)
    for i, total in enumerate(bottom):
        if total > 1.0:
            ax.text(
                x[i], total + offset_above,
                f"{_dfmt(total, 2)}%",
                ha="center", va="bottom",
                fontsize=10, fontweight="bold",
            )

    title: str = r"Desglose de Tipos de Fallo por Configuración \acro{RAG}"
    if not has_data:
        title += "\n(sin datos - requiere evaluación con juez v2.1+)"
    if title_suffix:
        title += f"\n{title_suffix}"

    ax.set_ylabel("Porcentaje de muestras (%)", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=10)
    ax.set_ylim(0, 122)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


    if "no_rag" in exp_names:
        fig.text(
            0.5, -0.04,
            r"Nota: la barra \emph{no\_rag} es 100\% \textit{retrieval\_failure} "
            "por restricción determinista (sin contexto disponible), no por "
            "decisión del juez.",
            ha="center", va="top", fontsize=10, style="italic",
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  failure_type_breakdown.png → %s", output_path)
    return output_path


def generate_rate_metrics_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "rate_metrics_comparison.png"

    exp_names: list[str] = _ordered_experiments(metrics)
    n_exp: int = len(exp_names)

    active_metrics: list[tuple[str, str]] = [
        (mk, label)
        for mk, label in RATE_METRICS
        if any(metrics[e].get(mk, 0.0) > 0.0 for e in exp_names)
    ]

    if not active_metrics:
        logger.warning(
            "Sin métricas de tasa disponibles (requiere evaluación con "
            "juez v2.1+), omitiendo rate_metrics_comparison"
        )
        return output_path

    n_metrics: int = len(active_metrics)
    x: Any = np.arange(n_metrics)
    width: float = min(0.84 / n_exp, 0.20)


    fig_w: float = max(12.0, n_metrics * 2.8 + n_exp * 0.5)
    fig, ax = plt.subplots(figsize=(fig_w, 7))

    for i, exp_name in enumerate(exp_names):
        values: list[float] = [
            metrics[exp_name].get(mk, 0.0) for mk, _ in active_metrics
        ]
        offset: float = (i - (n_exp - 1) / 2.0) * width
        bars = ax.bar(
            x + offset, values, width,
            label=EXPERIMENT_LABELS_GRAPH.get(exp_name, exp_name),
            color=EXPERIMENT_COLORS.get(exp_name, "#999999"),
            edgecolor="white",
            linewidth=0.5,
        )
        _stagger_bar_label_heights(
            bars, values, ax,
            fmt_fn=lambda v: f"{_dfmt(v, 2)}%",
            base_offset=1.8,
            stagger_step=2.8,
            bar_index=i,
            min_val=0.8,
            fontsize=10,
        )

    ax.set_ylabel("Porcentaje de muestras (%)", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    title: str = r"Métricas Booleanas de Calidad RAG (Juez LLM)"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in active_metrics], fontsize=15)
    ax.set_ylim(0, 128)
    ax.legend(loc="upper right", fontsize=15, ncol=max(1, n_exp // 4))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  rate_metrics_comparison.png → %s", output_path)
    return output_path


def generate_overconfidence_chart(
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    title_suffix: str = "",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "overconfidence_chart.png"


    ordered: list[str] = sorted(
        metrics.keys(),
        key=lambda c: metrics[c].get("overconfidence_rate", 0.0),
        reverse=True,
    )
    values: list[float] = [metrics[c].get("overconfidence_rate", 0.0) for c in ordered]
    labels: list[str] = [EXPERIMENT_LABELS_GRAPH.get(c, c) for c in ordered]
    colors: list[str] = [EXPERIMENT_COLORS.get(c, "#999999") for c in ordered]

    fig, ax = plt.subplots(figsize=(11, max(5.0, len(ordered) * 0.65)))

    bars = ax.barh(labels, values, color=colors, edgecolor="white", linewidth=0.5)


    for bar, val in zip(bars, values):

        offset: float = max(1.0, max(values or [0]) * 0.015)
        ax.text(
            val + offset,
            bar.get_y() + bar.get_height() / 2.0,
            f"{_dfmt(val, 2)}%",
            va="center", ha="left",
            fontsize=10, fontweight="bold",
        )

    ax.set_xlabel("Tasa de alucinación (%) (< mejor)", fontsize=12)
    ax.xaxis.set_major_formatter(_es_func_formatter())
    title: str = "Tasa de Alucinación por Configuración"
    if title_suffix:
        title += f"\n{title_suffix}"
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(values or [0]) * 1.28 + 5)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  overconfidence_chart.png → %s", output_path)
    return output_path


def generate_cross_model_chart(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    output_dir: Path,
    metric_key: str = "faithfulness_mean",
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)

    model_names: list[str] = sorted(model_metrics.keys())


    all_configs: set[str] = set()
    for m in model_names:
        all_configs.update(model_metrics[m].keys())
    exp_names: list[str] = [e for e in EXPERIMENT_ORDER if e in all_configs]


    model_palette: list[str] = [
        "#E74C3C", "#3498DB", "#2ECC71", "#9B59B6",
        "#F39C12", "#1ABC9C", "#E67E22",
    ]
    model_colors: dict[str, str] = {
        m: model_palette[i % len(model_palette)]
        for i, m in enumerate(model_names)
    }

    n_models: int = len(model_names)
    n_exp: int = len(exp_names)
    y: Any = np.arange(n_exp)

    width: float = min(0.8 / n_models, 0.26)

    metric_label: str = (
        dict(QUALITY_METRICS).get(metric_key)
        or dict(RATE_METRICS).get(metric_key)
        or dict(FAILURE_METRICS).get(metric_key)
        or metric_key
    )


    fig_height: float = max(3.5, 0.42 * n_exp * n_models + 3.5)

    fig, ax = plt.subplots(figsize=(10.5, fig_height))

    for i, model_name in enumerate(model_names):
        values: list[float] = [
            model_metrics[model_name].get(exp, {}).get(metric_key, 0.0)
            for exp in exp_names
        ]
        offset: float = (i - (n_models - 1) / 2.0) * width
        bars = ax.barh(
            y + offset, values, width,
            label=model_name,
            color=model_colors[model_name],
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, val in zip(bars, values):
            if val > 0.5:
                ax.text(
                    bar.get_width() + 0.8,
                    bar.get_y() + bar.get_height() / 2.0,
                    _dfmt(val, 2),
                    ha="left", va="center",
                    fontsize=15,
                )


    _rate_metrics: frozenset[str] = frozenset({
        "overconfidence_rate",
        "answer_accuracy", "context_sufficiency_rate", "faithfulness_rate",
        "contradiction_rate", "retrieval_failure_rate", "generation_failure_rate",
        "combined_failure_rate", "uncertain_rate",
    })
    _unit_label: str = "%" if metric_key in _rate_metrics else "pts"
    ax.set_xlabel(f"{metric_label} (0-100 {_unit_label})", fontsize=15)
    ax.xaxis.set_major_formatter(_es_func_formatter())
    ax.set_title(
        f"Comparativa entre Modelos - {metric_label}\nDataset: {dataset}",
        fontsize=15, fontweight="bold",
    )
    ax.set_yticks(y)
    ax.set_yticklabels(
        [EXPERIMENT_LABELS_GRAPH.get(e, e) for e in exp_names],
        fontsize=15,
    )


    ax.invert_yaxis()

    _all_vals: list[float] = [
        model_metrics[m].get(exp, {}).get(metric_key, 0.0)
        for m in model_names for exp in exp_names
    ]
    _x_max: float = max(max(_all_vals or [0]) * 1.25 + 6, 50)
    ax.set_xlim(0, min(_x_max, 150))

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.88, 0.98),
        fontsize=15,
        borderaxespad=0,

    )
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    output_path: Path = output_dir / f"cross_model_{_safe_label(metric_key)}.png"


    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  cross_model_%s.png → %s", metric_key, output_path)
    return output_path


def generate_cross_model_rate_metrics_chart(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    output_dir: Path,
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "cross_model_rate_metrics.png"

    model_names: list[str] = sorted(model_metrics.keys())
    if not model_names:
        return output_path


    def _agg(model: str, metric_key: str) -> float:
        vals: list[float] = [
            cfg_metrics.get(metric_key, 0.0)
            for cfg_metrics in model_metrics[model].values()
            if cfg_metrics.get(metric_key, 0.0) > 0.0
        ]
        return float(np.mean(vals)) if vals else 0.0

    active_metrics: list[tuple[str, str]] = [
        (mk, label)
        for mk, label in RATE_METRICS
        if any(_agg(m, mk) > 0.0 for m in model_names)
    ]
    if not active_metrics:
        logger.warning(
            "Sin métricas de tasa cross-modelo, omitiendo cross_model_rate_metrics"
        )
        return output_path

    palette: list[str] = [
        "#E74C3C", "#3498DB", "#2ECC71", "#9B59B6",
        "#F39C12", "#1ABC9C", "#E67E22",
    ]
    colors: dict[str, str] = {
        m: palette[i % len(palette)] for i, m in enumerate(model_names)
    }

    n_metrics: int = len(active_metrics)
    n_models: int = len(model_names)
    x: Any = np.arange(n_metrics)
    if len(model_names) >= 3:
        width: float = min(3 / n_models, 0.30)
    else:
        width: float = min(0.7 / n_models, 0.40)

    fig_w: float = max(12.0, n_metrics * 2.8 + n_models * 0.5)
    fig, ax = plt.subplots(figsize=(fig_w, 7))
    for i, model in enumerate(model_names):
        values: list[float] = [_agg(model, mk) for mk, _ in active_metrics]
        offset: float = (i - (n_models - 1) / 2.0) * width
        bars = ax.bar(
            x + offset, values, width,
            label=model,
            color=colors[model],
            edgecolor="white",
            linewidth=0.5,
        )
        if len(model_names) >= 3:
            _stagger_bar_label_heights(
                bars, values, ax,
                fmt_fn=lambda v: f"{_dfmt(v, 2)}%",
                base_offset=1.5,
                stagger_step=2.0,
                bar_index=i,
                min_val=-1,
                fontsize=12,
            )
        else:
            _stagger_bar_label_heights(
                bars, values, ax,
                fmt_fn=lambda v: f"{_dfmt(v, 2)}%",
                base_offset=1.0,
                stagger_step=1.0,
                bar_index=i,
                min_val=-1,
                fontsize=14,
            )

    ax.set_ylabel("Porcentaje de muestras (%)", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    ax.set_title(
        "Métricas Booleanas Cross-Modelo (media entre configuraciones)\n"
        f"Dataset: {dataset}",
        fontsize=15, fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in active_metrics], fontsize=15)
    ax.set_ylim(0, 135)
    ax.legend(loc="upper right", fontsize=15)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  cross_model_rate_metrics.png → %s", output_path)
    return output_path


def generate_cross_model_failure_chart(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    output_dir: Path,
) -> Path:

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = output_dir / "cross_model_failure_breakdown.png"

    model_names: list[str] = sorted(model_metrics.keys())
    all_configs: set[str] = set()
    for m in model_names:
        all_configs.update(model_metrics[m].keys())
    exp_names: list[str] = [e for e in EXPERIMENT_ORDER if e in all_configs]
    if not exp_names or not model_names:
        return output_path

    n_exp: int = len(exp_names)
    n_models: int = len(model_names)
    x: Any = np.arange(n_exp)
    width: float = min(0.8 / n_models, 0.35)

    fig, ax = plt.subplots(
        figsize=(max(11.0, n_exp * 1.6), max(5.0, 0.5 * n_models + 4.5))
    )

    for i, model in enumerate(model_names):
        offset: float = (i - (n_models - 1) / 2.0) * width
        bottom: list[float] = [0.0] * n_exp
        for metric_key, metric_label in FAILURE_METRICS:
            vals: list[float] = [
                model_metrics[model].get(exp, {}).get(metric_key, 0.0)
                for exp in exp_names
            ]
            color: str = FAILURE_COLORS.get(metric_key, "#999999")
            ax.bar(
                x + offset, vals, width,
                bottom=bottom,
                label=metric_label if i == 0 else None,
                color=color,
                edgecolor="white",
                linewidth=0.5,
            )
            bottom = [b + v for b, v in zip(bottom, vals)]

        for xi, total in zip(x, bottom):
            short_name: str = (
                model.replace("llama3-", "L").replace("mistral-", "M").
                replace("llama3.2-latest", "L3.2")
            )
            ax.text(
                xi + offset, total + 1.2,
                short_name,
                ha="center", va="bottom", fontsize=12, color="#333333",
            )

    labels: list[str] = [EXPERIMENT_LABELS_GRAPH.get(e, e) for e in exp_names]
    ax.set_ylabel("Porcentaje de muestras (%)", fontsize=12)
    ax.yaxis.set_major_formatter(_es_func_formatter())
    ax.set_title(
        "Desglose de Tipos de Fallo Cross-Modelo\n"
        f"Dataset: {dataset}",
        fontsize=15, fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=10)
    ax.set_ylim(0, 120)
    ax.legend(loc="upper right", fontsize=10, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if "no_rag" in exp_names:
        fig.text(
            0.5, -0.04,
            r"Nota: no_rag muestra 100 % retrieval_failure "
            "por restricción determinista (sin contexto recuperado → retrieval_failure).",
            ha="center", va="top", fontsize=10, style="italic",
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info("  cross_model_failure_breakdown.png → %s", output_path)
    return output_path


def generate_cross_model_table(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    output_dir: Path,
    family: str,
) -> Path:

    output_dir.mkdir(parents=True, exist_ok=True)


    model_names: list[str] = sorted(model_metrics.keys())
    all_configs: set[str] = set()
    for m in model_names:
        all_configs.update(model_metrics[m].keys())
    exp_names: list[str] = [e for e in EXPERIMENT_ORDER if e in all_configs]

    col_format: str = "ll" + "r" * 4 + "c" * 2 + "r"
    header: str = (
        r"Configuración & Modelo"
        r" & \abbr{Correct}{Correct.\textsuperscript{c}}"
        r" & \abbr{Faith}{Faith.\textsuperscript{c}}"
        r" & \abbr{Global}{Global\textsuperscript{c}}"
        r" & \abbr{AnsRel}{AnsRel.\textsuperscript{c}}"
        r" & \abbr{Overconf}{Alucinación \%}"
        r" & \abbr{RetFail}{RetFail. \%}"
        r" & \abbr{Lat}{Lat. (ms)}"
    )

    family_caption: str = (
        "cribado medio" if family == FAMILY_MODEL_SELECTION
        else "campaña principal"
    )

    caption_text = (
        f"Comparativa entre modelos para el dataset {_latex_escape(dataset)} "
        f"en la familia experimental: {_latex_escape(family_caption)}. "
        r"Corrección, faithfulness, puntuación global, relevancia y alucinación "
        r"(escala 0-100). La relevancia de la respuesta y la alucinación aparecen juntas "
        r"porque una no explica la calidad sin la otra: \textit{no\_rag} "
        r"puntúa alto en relevancia pero alto también en alucinación, "
        r"lo que indica la aparición de una alucinación en la generación."
    )
    table_label = f"tab:{_safe_label(family)}_cross_model_{_safe_label(dataset)}"

    lines: list[str] = [
        "\\begin{table}[H]",
        "  \\centering",
        "  \\scriptsize",
        "  \\setlength{\\tabcolsep}{3pt}",
        "  \\renewcommand{\\arraystretch}{0.85}",
        "  \\resizebox{\\textwidth}{!}{%",
        f"  \\begin{{tabular}}{{{col_format}}}",
        "    \\toprule",
        f"    {header} \\\\",
        "    \\midrule",
    ]

    for exp_name in exp_names:
        exp_label: str = EXPERIMENT_LABELS.get(exp_name, exp_name)
        first: bool = True
        for model_name in model_names:
            cfg_metrics: dict[str, float] = (
                model_metrics[model_name].get(exp_name, {})
            )
            if not cfg_metrics:
                continue
            cor_val: float = cfg_metrics.get("correctness_mean", 0.0)
            faith_val: float = cfg_metrics.get("faithfulness_mean", 0.0)
            overall_val: float = cfg_metrics.get("overall_mean", 0.0)
            relev_val: float = cfg_metrics.get("answer_relevance_mean", 0.0)
            overconf_val: float = cfg_metrics.get("overconfidence_rate", 0.0)
            genfail_val: float = cfg_metrics.get("retrieval_failure_rate", 0.0)
            lat_val: float = cfg_metrics.get("latency_mean_ms", 0.0)
            cfg_cell: str = exp_label if first else ""
            first = False
            lines.append(
                f"    {cfg_cell} & {_latex_escape(model_name)} & "
                f"{_dfmt(cor_val, 2)} & {_dfmt(faith_val, 2)} & "
                f"{_dfmt(overall_val, 2)} & {_dfmt(relev_val, 2)} & "
                f"{_dfmt(overconf_val, 2)} & {_dfmt(genfail_val, 2)} & {lat_val:.0f} \\\\"
            )

        lines.append("    \\addlinespace[2pt]")

    lines += [
        "    \\bottomrule",
        "  \\end{tabular}%",
        "  }",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        "\\end{table}",
    ]

    output_path: Path = output_dir / "cross_model_table.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info("  cross_model_table.tex → %s", output_path)
    return output_path


def generate_cross_model_metric_table(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    output_dir: Path,
    metric_key: str,
    family: str,
) -> Path:

    output_dir.mkdir(parents=True, exist_ok=True)

    model_names: list[str] = sorted(model_metrics.keys())
    all_configs: set[str] = set()
    for m in model_names:
        all_configs.update(model_metrics[m].keys())
    exp_names: list[str] = [e for e in EXPERIMENT_ORDER if e in all_configs]

    metric_label: str = (
        dict(QUALITY_METRICS).get(metric_key)
        or dict(RATE_METRICS).get(metric_key)
        or dict(FAILURE_METRICS).get(metric_key)
        or metric_key
    )

    col_format: str = "l" + "c" * len(model_names)
    header_cells: list[str] = ["Configuración"] + [
        _latex_escape(m) for m in model_names
    ]
    header: str = " & ".join(header_cells)

    caption_text_one: str = (
        f"{_latex_escape(metric_label)} por modelo sobre "
        f"{_latex_escape(dataset)} (escala 0-100)."
    )
    caption_text_two: str = (
        f"{_latex_escape(metric_label)} por modelo sobre "
        f"{_latex_escape(dataset)} (escala 0-100 \\%)."
    )
    caption_text: str = caption_text_one if metric_label != "Alucinación (< mejor)" else caption_text_two
    table_label: str = (
        f"tab:{_safe_label(family)}_cross_model_"
        f"{_safe_label(metric_key)}_{_safe_label(dataset)}"
    )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"  \centering",
        r"  \scriptsize",
        r"  \setlength{\tabcolsep}{6pt}",
        r"  \renewcommand{\arraystretch}{0.95}",
        f"  \\begin{{tabular}}{{{col_format}}}",
        r"    \toprule",
        f"    {header} \\\\",
        r"    \midrule",
    ]
    for exp_name in exp_names:
        exp_label: str = EXPERIMENT_LABELS.get(exp_name, exp_name)
        row_cells: list[str] = [
            f"\\texttt{{{exp_label}}}"
        ]
        for model_name in model_names:
            val: float = (
                model_metrics[model_name]
                .get(exp_name, {})
                .get(metric_key, float("nan"))
            )
            if val != val:
                row_cells.append("--")
            else:
                row_cells.append(_dfmt(val, 2))
        lines.append("    " + " & ".join(row_cells) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        r"\end{table}",
    ]

    output_path: Path = (
        output_dir / f"cross_model_{_safe_label(metric_key)}_table.tex"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(
        "  cross_model_%s_table.tex → %s", metric_key, output_path
    )
    return output_path


def _family_output_folder(family: str) -> str:
    if family == FAMILY_MAIN_EXPERIMENT:
        return "main_experiments"
    if family == FAMILY_MODEL_SELECTION:
        return "model_selection"
    raise ValueError(
        f"Unsupported family for generate_charts.py: {family}. "
        "Combo sweeps are not supported by this script."
        "Combo sweeps must be generated with scripts/run_retriever_comparison.py."
    )


def generate_group_charts(
    family: str,
    dataset: str,
    model: str,
    metrics: dict[str, dict[str, float]],
    output_dir: Path,
    num_runs: int = 1,
    include_radar: bool = True,
    include_improvement: bool = True,
    include_rate_metrics: bool = True,
) -> list[Path]:


    group_root = (
            output_dir
            / _family_output_folder(family)
            / _safe_label(dataset)
            / _safe_label(model)
    )

    budget_macros = output_dir / "budget" / "budget_macros.tex"
    budget_table = output_dir / "budget" / "budget_table.tex"
    thesis_dir = group_root / "thesis_compact"
    appendix_dir = group_root / "appendix"
    diagnostics_dir = group_root / "diagnostics"
    raw_dir = group_root / "raw_evidence"

    for directory in (thesis_dir, appendix_dir, diagnostics_dir, raw_dir):
        directory.mkdir(parents=True, exist_ok=True)

    suffix = f"Dataset: {dataset} | Modelo: {model}"
    if num_runs > 1:
        suffix += f" | Media de {num_runs} ejecuciones"

    generated: list[Path] = []


    generated.append(generate_quality_chart(metrics, thesis_dir, title_suffix=suffix))
    generated.append(generate_failure_type_chart(metrics, thesis_dir, title_suffix=suffix))


    generate_latex_table(
        metrics,
        appendix_dir,
        dataset=dataset,
        model=model,
        family=family,
    )


    generated.append(generate_latency_chart(metrics, diagnostics_dir, title_suffix=suffix))

    if include_rate_metrics:
        generated.append(generate_rate_metrics_chart(metrics, diagnostics_dir, title_suffix=suffix))
        generated.append(generate_overconfidence_chart(metrics, diagnostics_dir, title_suffix=suffix))

    if include_radar:
        generated.append(generate_radar_chart(metrics, diagnostics_dir, title_suffix=suffix))

    if include_improvement:
        generated.append(generate_improvement_chart(metrics, diagnostics_dir, title_suffix=suffix))

    raw_path = raw_dir / "merged_metrics.json"
    raw_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    generated.append(raw_path)


    generated.extend(
        write_group_thesis_artifacts(
            family=family,
            dataset=dataset,
            model=model,
            metrics=metrics,
            thesis_dir=thesis_dir,
        )
    )

    generated.append(
        write_budget_macros(budget_macros)
    )
    generated.append(
        write_budget_table(budget_table)
    )

    return generated


def list_available_runs(log_dir: Path) -> None:

    try:
        summaries = discover_summaries(log_dir, include_families=None)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return


    runs_dir: Path = log_dir / "runs"
    orphans_skipped: int = 0
    filtered_summaries: list[dict[str, Any]] = []
    for s in summaries:
        rid: str = s.get("run_id", "")
        has_experiments: bool = bool(s.get("experiments"))
        run_dir_exists: bool = (runs_dir / rid).exists() if rid else False
        if not has_experiments and not run_dir_exists:
            orphans_skipped += 1
            logger.debug("Skipping orphan summary (no run dir, 0 experiments): %s", rid)
            continue
        filtered_summaries.append(s)
    summaries = filtered_summaries


    for s in summaries:
        s["_experiment_family"] = _infer_experiment_family_for_display(
            s, log_dir
        )

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = group_summaries(summaries)

    print()
    print("=" * 108)
    print("  EJECUCIONES DISPONIBLES EN logs/")
    print("=" * 108)

    for (family, dataset, model), run_list in sorted(groups.items()):

        print()
        print(
            f"  [{family}]  dataset={dataset}  model={model}"
            f"  ({len(run_list)} run{'s' if len(run_list) != 1 else ''})"
        )
        print("  " + "─" * 104)


        for s in run_list:
            run_id: str = s.get("run_id") or "?"
            ts: str = _summary_timestamp(s) or "?"
            experiments: dict[str, Any] = s.get("experiments", {})
            exp_ok: int = len([
                e for e in experiments.values()
                if e.get("status", "") in ("completed", "partial")
            ])
            exp_total: int = len(experiments)


            total_q: int = sum(
                int(e.get("num_queries", 0))
                for e in experiments.values()
                if e.get("status", "") in ("completed", "partial")
            )
            total_q_str: str = f"  {total_q} q total" if total_q else ""

            print(
                f"    {run_id:<60} "
                f"{ts}  "
                f"({exp_ok}/{exp_total} exps OK){total_q_str}"
            )


            if experiments:

                ordered_keys: list[str] = [
                    k for k in EXPERIMENT_ORDER if k in experiments
                ]
                for k in sorted(experiments):
                    if k not in ordered_keys:
                        ordered_keys.append(k)


                STATUS_SYMBOL: dict[str, str] = {
                    "completed": "[OK]",
                    "partial":   "~",
                    "failed":    "[FAIL]",
                    "skipped":   "-",
                }
                cells: list[str] = []
                for cfg_key in ordered_keys:
                    exp_data: dict[str, Any] = experiments[cfg_key]
                    nq: int = int(exp_data.get("num_queries", 0))
                    status_raw: str = exp_data.get("status", "?")
                    sym: str = STATUS_SYMBOL.get(status_raw, "?")
                    cells.append(f"{sym} {cfg_key:<32} {nq:>4} q")


                cols: int = 3
                cell_width: int = 42
                for row_start in range(0, len(cells), cols):
                    row_cells: list[str] = cells[row_start : row_start + cols]
                    print("      " + "  │  ".join(f"{c:<{cell_width}}" for c in row_cells))
                print()

    print()
    print("─" * 108)
    if orphans_skipped:
        print(
            f"  ({orphans_skipped} orphan summary file{'s' if orphans_skipped != 1 else ''} skipped"
            " - run dir missing + 0 experiments)"
        )
    print("Para generar gráficas de un grupo específico:")
    print("  python3 scripts/generate_charts.py --dataset rag_domain --model llama3-8b")
    print()


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generador de gráficas de tesis a partir de logs de experimentos RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 scripts/generate_charts.py                        # todas las ejecuciones
  python3 scripts/generate_charts.py --list-runs            # listar disponibles
  python3 scripts/generate_charts.py --dataset rag_domain   # filtrar por dataset
  python3 scripts/generate_charts.py --model llama3-8b      # filtrar por modelo
  python3 scripts/generate_charts.py --strategy latest      # usar solo la ejecución más reciente
        """,
    )
    parser.add_argument(
        "--log-dir", type=Path, default=LOG_DIR,
        help=f"Directorio con los logs (default: {LOG_DIR})",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=OUTPUT_DIR,
        help=f"Directorio de salida (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--dataset", type=str, default="",
        help="Filtrar por dataset (e.g. rag_domain, hotpotqa)",
    )
    parser.add_argument(
        "--model", type=str, default="",
        help="Filtrar por modelo (e.g. llama3-8b, mistral-7b)",
    )
    parser.add_argument(
        "--strategy", type=str, default="average", choices=["latest", "average"],
        help=(
            "Estrategia para múltiples ejecuciones del mismo grupo: "
            "'latest' = usar la más reciente, "
            "'average' = promediar todas las ejecuciones del grupo (default)."
        ),
    )
    parser.add_argument(
        "--list-runs", action="store_true",
        help="Listar ejecuciones disponibles y salir sin generar gráficas.",
    )
    parser.add_argument(
        "--skip-cross-model", action="store_true",
        help="No generar comparativas entre modelos.",
    )
    parser.add_argument(
        "--include-family",
        action="append",
        default=None,
        choices=[
            FAMILY_MAIN_EXPERIMENT,
            FAMILY_MODEL_SELECTION,
        ],
        help=(
            "Experiment family to include. Can be passed multiple times. "
            "Default: main_experiment only."
        ),
    )
    parser.add_argument(
        "--all-families",
        action="store_true",
        help=(
            "Include all chart-supported families "
            "(main_experiment and model_selection). "
            "combo_sweep runs are not supported by this script."
            "combo_sweep remains handled by run_retriever_comparison.py."
        ),
    )
    parser.add_argument(
        "--no-radar",
        action="store_true",
        help="Do not generate radar charts.",
    )
    parser.add_argument(
        "--no-improvement",
        action="store_true",
        help="Do not generate improvement charts.",
    )
    parser.add_argument(
        "--no-rate-metrics",
        action="store_true",
        help="Do not generate rate metric charts.",
    )
    parser.add_argument(
        "--no-retriever-comparison",
        action="store_true",
        help=(
            "Skip the run_retriever_comparison --skip-eval --generate-only call. "
            "When NOT set, combo-sweep thesis artifacts are regenerated from existing "
            "logs as the first step (before per-model charts and component effects). "
            "This is intentionally the first step so that model-selection combo "
            "artifacts are available when the thesis input{} includes them."
        ),
    )
    parser.add_argument(
        "--no-chunking-table",
        action="store_true",
        help=(
            "Do not invoke scripts/compare_chunking.py to (re)generate the "
            "chunking efficiency LaTeX table under "
            "output/thesis/main_experiments/chunking/."
        ),
    )
    parser.add_argument(
        "--no-component-effects",
        action="store_true",
        help=(
            "Skip the isolated component-effect analysis "
            "(scripts/compare_component_effects.py).  When NOT set, the "
            "component-effect tables, charts, CSVs, Markdown and "
            "interpretation .tex files are regenerated under "
            "output/thesis/main_experiments/component_effects/."
        ),
    )
    return parser.parse_args()


def main() -> int:

    args: argparse.Namespace = parse_args()

    if args.list_runs:
        list_available_runs(args.log_dir)
        return 0

    logger.info("=" * 60)
    logger.info("GENERADOR DE GRÁFICAS - TFG RAG")
    logger.info("=" * 60)
    logger.info("Log dir:    %s", args.log_dir)
    logger.info("Output dir: %s", args.output_dir)
    logger.info("Estrategia: %s", args.strategy)


    try:
        if args.all_families:
            include_families = CHART_SUPPORTED_FAMILIES
        elif args.include_family:
            include_families = args.include_family
        else:
            include_families = DEFAULT_INCLUDED_FAMILIES
        summaries: list[dict[str, Any]] = discover_summaries(
            args.log_dir,
            include_families=include_families,
        )
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = group_summaries(summaries)


    if args.dataset:
        groups = {k: v for k, v in groups.items() if k[1] == args.dataset}
        if not groups:
            logger.error(
                "No se encontraron ejecuciones para el dataset '%s'. "
                "Usa --list-runs para ver los disponibles.",
                args.dataset,
            )
            return 1

    if args.model:
        groups = {k: v for k, v in groups.items() if k[2] == args.model}
        if not groups:
            logger.error(
                "No se encontraron ejecuciones para el modelo '%s'. "
                "Usa --list-runs para ver los disponibles.",
                args.model,
            )
            return 1

    logger.info("Grupos (dataset, modelo) a procesar: %d", len(groups))

    all_generated: list[Path] = []


    if not getattr(args, "no_retriever_comparison", False):
        try:
            logger.info(
                "Regenerando artefactos de comparativa retriever×reranker "
                "(--skip-eval --generate-only)...",
            )
            _run_retriever_comparison([
                "--skip-eval",
                "--generate-only",
                "--log-file", "/dev/null",
            ])
        except SystemExit as exc:
            if exc.code not in (0, None):
                logger.warning(
                    "run_retriever_comparison salió con código %s; "
                    "continuando con el resto del pipeline de gráficas.",
                    exc.code,
                )
        except Exception as exc:
            logger.warning(
                "run_retriever_comparison falló (%s); continuando con el "
                "resto del pipeline de gráficas.",
                exc,
            )


    for (family, dataset, model), run_list in sorted(groups.items()):
        logger.info(
            "Procesando: dataset='%s'  modelo='%s'  (%d ejecuciones)",
            dataset, model, len(run_list),
        )
        metrics: dict[str, dict[str, float]] = merge_group_summaries(
            run_list, strategy=args.strategy,
        )
        if not metrics:
            logger.warning("  Sin experimentos exitosos, omitiendo grupo")
            continue
        generated = generate_group_charts(
            family=family,
            dataset=dataset,
            model=model,
            metrics=metrics,
            output_dir=args.output_dir,
            num_runs=len(run_list),
            include_radar=not args.no_radar,
            include_improvement=not args.no_improvement,
            include_rate_metrics=not args.no_rate_metrics,
        )
        all_generated.extend(generated)


    if not args.skip_cross_model:

        family_dataset_model_metrics: dict[
            tuple[str, str],
            dict[str, dict[str, dict[str, float]]]
        ] = defaultdict(dict)

        for (family, dataset, model), run_list in groups.items():
            m = merge_group_summaries(run_list, strategy=args.strategy)
            if m:
                family_dataset_model_metrics[(family, dataset)][model] = m

        for (family, dataset), model_data in family_dataset_model_metrics.items():
            if len(model_data) < 2:
                continue

            cross_dir = (
                    args.output_dir
                    / _family_output_folder(family)
                    / "cross_model"
                    / _safe_label(dataset)
                    / "thesis_compact"
            )
            cross_dir.mkdir(parents=True, exist_ok=True)
            for metric_key in (
                "faithfulness_mean",
                "answer_relevance_mean",
                "correctness_mean",
                "overconfidence_rate",
                "answer_accuracy",
                "context_sufficiency_rate",
                "faithfulness_rate",
                "contradiction_rate",
            ):
                generated_path: Path = generate_cross_model_chart(
                    model_metrics=model_data,
                    dataset=dataset,
                    output_dir=cross_dir,
                    metric_key=metric_key,
                )
                all_generated.append(generated_path)

                all_generated.append(
                    generate_cross_model_metric_table(
                        model_metrics=model_data,
                        dataset=dataset,
                        output_dir=cross_dir,
                        metric_key=metric_key,
                        family=family,
                    )
                )


            all_generated.append(
                generate_cross_model_rate_metrics_chart(
                    model_metrics=model_data,
                    dataset=dataset,
                    output_dir=cross_dir,
                )
            )
            all_generated.append(
                generate_cross_model_failure_chart(
                    model_metrics=model_data,
                    dataset=dataset,
                    output_dir=cross_dir,
                )
            )


            all_generated.append(
                generate_cross_model_table(
                    model_metrics=model_data,
                    dataset=dataset,
                    output_dir=cross_dir,
                    family=family,
                )
            )


            all_generated.extend(
                write_cross_model_thesis_artifacts(
                    family=family,
                    dataset=dataset,
                    model_metrics=model_data,
                    cross_dir=cross_dir,
                )
            )


    if not getattr(args, "no_component_effects", False):
        comp_root: Path = (
            args.output_dir
            / "main_experiments"
            / "component_effects"
        )
        try:
            logger.info(
                "Generando análisis de efectos aislados de componentes...",
            )
            _run_component_effects_analysis(["--min-samples", "600"])
            for effect in ("chunking", "reranking", "grounding", "retriever"):
                for artifact_name in (
                    f"{effect}_effect.csv",
                    f"{effect}_effect.md",
                    f"{effect}_effect_aggregate.md",
                    f"{effect}_effect_table.tex",
                    f"{effect}_effect_interpretation.tex",
                    f"{effect}_effect_chart.png",
                ):
                    ap2: Path = comp_root / effect / artifact_name
                    if ap2.exists():
                        all_generated.append(ap2)
        except Exception as exc:
            logger.warning(
                "compare_component_effects falló (%s); continuando con el resto "
                "del pipeline de gráficas.",
                exc,
            )

    logger.info("=" * 60)
    logger.info("Archivos generados: %d", len(all_generated))
    for p in all_generated:
        logger.info("  %s", p)
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
