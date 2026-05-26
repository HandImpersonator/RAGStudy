from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


FAMILY_MAIN_EXPERIMENT: str = "main_experiment"
FAMILY_MODEL_SELECTION: str = "model_selection"
FAMILY_COMBO_SWEEP: str = "combo_sweep"


EXPERIMENT_ORDER: list[str] = [
    "no_rag",

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

FINAL_SELECTED_GENERATOR_MODELS: set[str] = {
    "llama3-8b",
    "mistral-7b",
}

FINAL_DISCARDED_GENERATOR_MODELS: set[str] = {
    "llama3.2-latest",
}


def _dfmt(value: float, decimals: int = 2) -> str:

    return f"{value:.{decimals}f}".replace(".", ",")


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
def _safe_label(text: str) -> str:

    for char in (":", "/", "\\", " ", "@"):
        text = text.replace(char, "_")
    return text


def _label_slug(*parts: Any) -> str:

    cleaned: list[str] = []

    for part in parts:
        raw = str(part or "").strip()
        if not raw:
            continue

        slug = _safe_label(raw)
        for char in (".", "-", " "):
            slug = slug.replace(char, "_")

        while "__" in slug:
            slug = slug.replace("__", "_")

        slug = slug.strip("_")
        if slug:
            cleaned.append(slug)

    return "_".join(cleaned)


def _tab_label(*parts: Any) -> str:

    return "tab:" + _label_slug(*parts)


STUDENT_HOURS = Decimal("450")
STUDENT_HOURLY_RATE_EUR = Decimal("15")

LOCAL_DEVELOPMENT_EQUIPMENT_EUR = Decimal("1200")
UNIVERSITY_SERVER_EUR = Decimal("0")
REMOTE_DEDICATED_SERVER_EUR = Decimal("150")
FREE_SOFTWARE_EUR = Decimal("0")
OPEN_MODELS_EUR = Decimal("0")
PUBLIC_DATASETS_EUR = Decimal("0")
LLM_JUDGE_API_EUR = Decimal("180")


@dataclass(frozen=True)
class BudgetItem:
    concept: str
    amount: Decimal
    qualifier: str
    description: str
    include_in_imputed_total: bool = True
    include_in_direct_total: bool = False
    approximate: bool = False


def _format_eur(
    amount: Decimal,
    approximate: bool = False,
    qualifier: str = "",
    nbsp: bool = True,
) -> str:
    euros = int(amount)
    rendered = f"{euros:,}".replace(",", ".")

    prefix = r"$\approx$" if approximate else ""
    space = r"\," if nbsp else " "
    suffix = f" {qualifier}" if qualifier else ""

    return f"{prefix}{rendered}{space}\\euro{{}}{suffix}"


def _format_eur_prose(amount: Decimal, approximate: bool = False) -> str:
    euros = int(amount)
    rendered = f"{euros:,}".replace(",", ".")

    if approximate:
        return f"aproximadamente {rendered}\\,\\euro{{}} "

    return f"{rendered}\\,\\euro{{}} "


def _budget_imputed_total(items: list[BudgetItem]) -> Decimal:
    return sum(
        (item.amount for item in items if item.include_in_imputed_total),
        Decimal("0"),
    )


def _budget_direct_total(items: list[BudgetItem]) -> Decimal:
    return sum(
        (item.amount for item in items if item.include_in_direct_total),
        Decimal("0"),
    )


def _budget_item_by_concept(items: list[BudgetItem], concept: str) -> BudgetItem:
    for item in items:
        if item.concept == concept:
            return item

    raise ValueError(f"Budget item not found: {concept}")


def _budget_items() -> list[BudgetItem]:
    student_labor = STUDENT_HOURS * STUDENT_HOURLY_RATE_EUR

    return [
        BudgetItem(
            concept="Horas de trabajo del estudiante",
            amount=student_labor,
            qualifier="",
            description=(
                f"{int(STUDENT_HOURS)} horas estimadas a "
                f"{int(STUDENT_HOURLY_RATE_EUR)} \\euro{{}}/hora. Incluye "
                "investigación, diseño, implementación, experimentación, "
                "análisis y redacción."
            ),
        ),
        BudgetItem(
            concept="Equipo local de desarrollo",
            amount=LOCAL_DEVELOPMENT_EQUIPMENT_EUR,
            qualifier="imputados",
            description=(
                "Equipo personal utilizado para desarrollo y ejecución local. "
                "No supone compra directa para el proyecto."
            ),
        ),
        BudgetItem(
            concept="Servidor universitario",
            amount=UNIVERSITY_SERVER_EUR,
            qualifier="directos",
            description=(
                "Recurso proporcionado por la universidad. Se usa para ejecutar "
                "modelos mediante Ollama."
            ),
            include_in_imputed_total=False,
            include_in_direct_total=True,
        ),
        BudgetItem(
            concept="Servidor dedicado remoto",
            amount=REMOTE_DEDICATED_SERVER_EUR,
            qualifier="directos",
            description=(
                "Coste directo del servidor alquilado TensorDock tras la pérdida de acceso "
                "al servidor universitario. La máquina permitió repetir la "
                "preparación del entorno, reconstruir cachés, regenerar "
                "resultados ya perdidos y completar las ejecuciones "
                "experimentales pendientes."
            ),
            include_in_direct_total=True,
        ),
        BudgetItem(
            concept="Software libre y bibliotecas",
            amount=FREE_SOFTWARE_EUR,
            qualifier="directos",
            description=(
                "Python, Fast\\acro{API}, \\acro{FAISS}, sentence-transformers, "
                "herramientas de evaluación y scripts propios."
            ),
            include_in_imputed_total=False,
            include_in_direct_total=True,
        ),
        BudgetItem(
            concept="Modelos abiertos",
            amount=OPEN_MODELS_EUR,
            qualifier="directos",
            description=(
                "Modelos servidos mediante Ollama y modelos de embeddings y "
                "re-ranking de uso abierto según sus licencias."
            ),
            include_in_imputed_total=False,
            include_in_direct_total=True,
        ),
        BudgetItem(
            concept="Datasets públicos",
            amount=PUBLIC_DATASETS_EUR,
            qualifier="directos",
            description=(
                "Uso de datasets y corpus disponibles públicamente para "
                "investigación."
            ),
            include_in_imputed_total=False,
            include_in_direct_total=True,
        ),
        BudgetItem(
            concept="Evaluación externa con \\acro{LLM} juez",
            amount=LLM_JUDGE_API_EUR,
            qualifier="directos",
            description=(
                "Coste real acumulado del juez \\acro{LLM} "
                "(\\acro{API} comercial de pago de OpenAI, modelo "
                "\\texttt{\\abbr{GPT}{gpt}-5.4-mini}) sobre todas las muestras "
                "evaluadas a lo largo del proyecto."
            ),
            include_in_direct_total=True,
            approximate=True,
        ),
    ]


latex_escape = _latex_escape
safe_label = _safe_label


_THESIS_QUALITY_WEIGHTS = {
    "correctness_mean": 0.35,
    "faithfulness_mean": 0.35,
    "context_support_mean": 0.20,
    "answer_relevance_mean": 0.10,
}


FINAL_SCREENING_CONFIGS: list[str] = [
    "no_rag",
    "baseline_s",
    "baseline_s_rr",
    "baseline_s_rr_grounded",
    "optimized_s",
    "optimized_s_rr",
    "optimized_s_rr_grounded",
]

FINAL_SELECTED_RAG_CONFIGS: set[str] = {
    cfg for cfg in FINAL_SCREENING_CONFIGS if cfg != "no_rag"
}

BM25_FAISS_CROSS_MODEL_PAIRS: list[tuple[str, str]] = [
    ("baseline_k", "baseline_s"),
    ("baseline_k_rr", "baseline_s_rr"),
    ("baseline_k_grounded", "baseline_s_grounded"),
    ("baseline_k_rr_grounded", "baseline_s_rr_grounded"),
    ("optimized_k", "optimized_s"),
    ("optimized_k_rr", "optimized_s_rr"),
    ("optimized_k_grounded", "optimized_s_grounded"),
    ("optimized_k_rr_grounded", "optimized_s_rr_grounded"),
]


BM25_CLEAR_SCORE_GAIN_PTS: float = 3.0
BM25_HIGH_LATENCY_RATIO: float = 3.0


def _thesis_quality_score(m: dict[str, float]) -> float:

    return sum(
        float(m.get(key, 0.0)) * weight
        for key, weight in _THESIS_QUALITY_WEIGHTS.items()
    )


def _mean_float(values: list[float]) -> float:

    return (sum(values) / len(values)) if values else 0.0


def _sample_std_float(values: list[float]) -> float:

    if len(values) < 2:
        return 0.0

    mean: float = _mean_float(values)
    variance: float = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def _score_values_for_config(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    config_name: str,
) -> list[float]:

    values: list[float] = []

    for config_metrics_by_model in model_metrics.values():
        cfg_metrics: dict[str, float] | None = config_metrics_by_model.get(config_name)
        if cfg_metrics:
            values.append(_thesis_quality_score(cfg_metrics))

    return values


def _metric_values_for_config(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    config_name: str,
    metric_key: str,
) -> list[float]:

    values: list[float] = []

    for config_metrics_by_model in model_metrics.values():
        cfg_metrics: dict[str, float] | None = config_metrics_by_model.get(config_name)
        if not cfg_metrics:
            continue

        raw_value = cfg_metrics.get(metric_key)
        if isinstance(raw_value, (int, float)):
            values.append(float(raw_value))

    return values


def _cross_model_config_rows(
    model_metrics: dict[str, dict[str, dict[str, float]]],
) -> list[dict[str, Any]]:

    all_configs: set[str] = set()
    for per_model_metrics in model_metrics.values():
        all_configs.update(per_model_metrics.keys())

    ordered_configs: list[str] = [
        cfg for cfg in EXPERIMENT_ORDER if cfg in all_configs
    ]

    for cfg in sorted(all_configs):
        if cfg not in ordered_configs:
            ordered_configs.append(cfg)

    rows: list[dict[str, Any]] = []

    for cfg in ordered_configs:
        score_values: list[float] = _score_values_for_config(model_metrics, cfg)
        if not score_values:
            continue

        if cfg == "no_rag":
            role = "control"
            decision = "Control"
        elif cfg in FINAL_SELECTED_RAG_CONFIGS:
            role = "selected"
            decision = "Seleccionada"
        else:
            role = "discarded"
            decision = "Excluida"

        rows.append({
            "config": cfg,
            "score_mean": _mean_float(score_values),
            "score_std": _sample_std_float(score_values),
            "correctness_mean": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "correctness_mean")
            ),
            "faithfulness_mean": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "faithfulness_mean")
            ),
            "answer_relevance_mean": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "answer_relevance_mean")
            ),
            "overall_mean": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "overall_mean")
            ),
            "generation_failure_rate": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "generation_failure_rate")
            ),
            "latency_mean_ms": _mean_float(
                _metric_values_for_config(model_metrics, cfg, "latency_mean_ms")
            ),
            "n_models": len(score_values),
            "role": role,
            "decision": decision,
        })

    selected_order: dict[str, int] = {
        cfg: idx for idx, cfg in enumerate(FINAL_SCREENING_CONFIGS)
    }

    def _sort_key(row: dict[str, Any]) -> tuple[int, int, float]:
        cfg = str(row["config"])

        if cfg == "no_rag":
            return (0, 0, 0.0)

        if cfg in FINAL_SELECTED_RAG_CONFIGS:
            return (1, selected_order.get(cfg, 999), 0.0)

        return (2, 0, -float(row["score_mean"]))

    rows.sort(key=_sort_key)
    return rows


def _rank_models_for_cross_model_selection(
    model_metrics: dict[str, dict[str, dict[str, float]]],
) -> list[dict[str, Any]]:

    rows: list[dict[str, Any]] = []

    for model_name, cfg_map in model_metrics.items():
        selected_metrics: list[dict[str, float]] = [
            cfg_map[cfg]
            for cfg in FINAL_SELECTED_RAG_CONFIGS
            if cfg in cfg_map
        ]

        if not selected_metrics:
            selected_metrics = [
                metrics for cfg, metrics in cfg_map.items()
                if cfg != "no_rag"
            ]

        scores: list[float] = [
            _thesis_quality_score(m) for m in selected_metrics
        ]

        latencies: list[float] = [
            float(m.get("latency_mean_ms", 0.0))
            for m in selected_metrics
            if isinstance(m.get("latency_mean_ms", 0.0), (int, float))
        ]

        if not scores:
            continue

        rows.append({
            "model": model_name,
            "score_mean": _mean_float(scores),
            "latency_mean_ms": _mean_float(latencies),
            "n_configs": len(scores),
        })

    rows.sort(
        key=lambda r: (
            -float(r["score_mean"]),
            float(r["latency_mean_ms"]),
        )
    )

    return rows


def _write_model_selection_decision(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = _rank_models_for_cross_model_selection(
        model_metrics
    )

    if not rows:
        return _write_todo_tex(
            out,
            "regenerar model_selection_decision.tex con scripts/generate_charts.py "
            "cuando existan logs model_selection cross-model.",
        )

    caption_text: str = (
        r"Selección cross-model del modelo generativo para la campaña principal "
        f"sobre {_latex_escape(dataset)}. La puntuación media se calcula sobre el "
        r"conjunto compacto de configuraciones \acro{RAG} seleccionadas; "
        r"\texttt{no\_rag} queda excluido porque es control experimental."
    )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{0.9}",
        r"\begin{adjustbox}{max width=0.80\textwidth}",
        r"\begin{tabular}{lcccl}",
        r"\toprule",
        (
            r"\textbf{Modelo} & "
            r"\textbf{Puntuación media} & "
            r"\textbf{Latencia media (ms)} & "
            r"\textbf{Configuraciones} & "
            r"\textbf{Decisión} \\"
        ),
        r"\midrule",
    ]

    for idx, row in enumerate(rows):
        decision: str = "Seleccionado" if row.get("model") != "llama3.2-latest" else "Excluido"
        lines.append(
            f"\\texttt{{{_latex_escape(row['model'])}}} & "
            f"{_dfmt(float(row['score_mean']), 2)} & "
            f"{float(row['latency_mean_ms']):.0f} & "
            f"{int(row['n_configs'])} & "
            f"{decision} \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{_tab_label(FAMILY_MODEL_SELECTION, 'model_decision', dataset)}}}",
        r"\end{table}",
        "",
        (
            r"\noindent\emph{Nota:} La puntuación media se calcula con el "
            r"criterio de cribado definido en la "
            r"Sección~\ref{subsec:criterio_agregacion_cribado}: "
            r"$P_{\mathrm{cribado/compuesto}} = "
            r"0.35\cdot\mathrm{Correctness} + "
            r"0.35\cdot\mathrm{Faithfulness} + "
            r"0.20\cdot\mathrm{ContextSupport} + "
            r"0.10\cdot\mathrm{AnswerRelevance}$. "
            r"Esta tabla separa la decisión de modelo de la decisión de "
            r"configuración."
        ),
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _bm25_faiss_cross_model_reading(
    delta_score: float,
    latency_ratio: float,
) -> str:

    if delta_score <= 0.0 and latency_ratio >= 1.0:
        return r"\acro{FAISS} seleccionada."

    if (
        latency_ratio >= BM25_HIGH_LATENCY_RATIO
        and delta_score < BM25_CLEAR_SCORE_GAIN_PTS
    ):
        return r"\acro{BM25} descartado por coste."

    if (
        latency_ratio >= BM25_HIGH_LATENCY_RATIO
        and delta_score >= BM25_CLEAR_SCORE_GAIN_PTS
    ):
        return r"\acro{BM25} mejora, pero no compensa coste."

    if delta_score >= BM25_CLEAR_SCORE_GAIN_PTS:
        return r"\acro{BM25} aporta mejora de calidad."

    return r"Diferencia no concluyente."


def _bm25_faiss_cross_model_pair_rows(
    model_metrics: dict[str, dict[str, dict[str, float]]],
) -> list[dict[str, Any]]:

    config_rows = _cross_model_config_rows(model_metrics)

    by_config: dict[str, dict[str, Any]] = {
        str(row["config"]): row for row in config_rows
    }

    pair_rows: list[dict[str, Any]] = []

    for bm25_cfg, faiss_cfg in BM25_FAISS_CROSS_MODEL_PAIRS:
        bm25_row = by_config.get(bm25_cfg)
        faiss_row = by_config.get(faiss_cfg)

        if bm25_row is None or faiss_row is None:
            continue

        bm25_score: float = float(bm25_row["score_mean"])
        faiss_score: float = float(faiss_row["score_mean"])
        bm25_latency: float = float(bm25_row["latency_mean_ms"])
        faiss_latency: float = float(faiss_row["latency_mean_ms"])

        delta_score: float = bm25_score - faiss_score

        latency_ratio: float = (
            bm25_latency / faiss_latency
            if faiss_latency > 0.0
            else 0.0
        )

        pair_rows.append({
            "bm25_cfg": bm25_cfg,
            "faiss_cfg": faiss_cfg,
            "bm25_score": bm25_score,
            "faiss_score": faiss_score,
            "delta_score": delta_score,
            "bm25_latency": bm25_latency,
            "faiss_latency": faiss_latency,
            "latency_ratio": latency_ratio,
            "reading": _bm25_faiss_cross_model_reading(
                delta_score=delta_score,
                latency_ratio=latency_ratio,
            ),
        })

    return pair_rows


def _write_config_screening_cross_model_decision(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = _cross_model_config_rows(model_metrics)

    rows = sorted(
        rows,
        key=lambda row: float(row["score_mean"]),
        reverse=True,
    )

    if not rows:
        return _write_todo_tex(
            out,
            "regenerar config_screening_cross_model_decision.tex con "
            "scripts/generate_charts.py cuando existan logs model_selection.",
        )


    if dataset.lower() == "hotpotqa":
        lines: list[str] = [
            r"\begin{table}[H]",
            r"\centering",
            r"\scriptsize",
            r"\setlength{\tabcolsep}{2pt}",
            r"\renewcommand{\arraystretch}{0.9}",
            r"\begin{adjustbox}{max width=0.96\textwidth}",
            r"\begin{tabular}{lcrrrr}",
            r"\toprule",
            (
                r"\textbf{Configuración} & "
                r"\textbf{Puntuación media} & "
                r"\textbf{\abbr{DesvScore}{Desv.\,score}} & "
                r"\textbf{\abbr{Correct}{Correct.\textsuperscript{c}}} & "
                r"\textbf{\abbr{Faith}{Faith.\textsuperscript{c}}} & "
                r"\textbf{\abbr{AnsRel}{AnsRel.\textsuperscript{c}}} \\"
            ),
            r"\midrule",
        ]

        for row in rows:
            lines.append(
                f"\\texttt{{{_latex_escape(row['config'])}}} & "
                f"{_dfmt(float(row['score_mean']), 2)} & "
                f"{_dfmt(float(row['score_std']), 2)} & "
                f"{_dfmt(float(row['correctness_mean']), 2)} & "
                f"{_dfmt(float(row['faithfulness_mean']), 2)} & "
                f"{_dfmt(float(row.get('answer_relevance_mean', 0.0)), 2)} \\\\"
            )

        lines += [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{adjustbox}",
            (
                r"\caption{Cribado medio cross-model de configuraciones "
                rf"\acro{{RAG}} sobre {_latex_escape(dataset)} "
                r"(ordenado por puntuación media descendente). "
                r"\texttt{no\_rag} se conserva como control experimental.}"
            ),
            f"\\label{{{_tab_label(FAMILY_MODEL_SELECTION, 'config_screening_cross_model_decision', dataset)}}}",
            r"\end{table}",
            "",
        ]

    else:
        lines = [
            r"\begin{table}[H]",
            r"\centering",
            r"\scriptsize",
            r"\setlength{\tabcolsep}{2pt}",
            r"\renewcommand{\arraystretch}{0.9}",
            r"\begin{adjustbox}{max width=0.96\textwidth}",
            r"\begin{tabular}{lcrrrrrcl}",
            r"\toprule",
            (
                r"\textbf{Configuración} & "
                r"\textbf{Puntuación media} & "
                r"\textbf{\abbr{DesvScore}{Desv.\,score}} & "
                r"\textbf{\abbr{Correct}{Correct.\textsuperscript{c}}} & "
                r"\textbf{\abbr{Faith}{Faith.\textsuperscript{c}}} & "
                r"\textbf{\abbr{Global}{Global\textsuperscript{c}}} & "
                r"\textbf{\abbr{GenFail}{GenFail.\,\%}} & "
                r"\textbf{\abbr{LatMedia}{Lat.\,media (ms)}} & "
                r"\textbf{Decisión} \\"
            ),
            r"\midrule",
        ]

        for row in rows:
            lines.append(
                f"\\texttt{{{_latex_escape(row['config'])}}} & "
                f"{_dfmt(float(row['score_mean']), 2)} & "
                f"{_dfmt(float(row['score_std']), 2)} & "
                f"{_dfmt(float(row['correctness_mean']), 2)} & "
                f"{_dfmt(float(row['faithfulness_mean']), 2)} & "
                f"{_dfmt(float(row['overall_mean']), 2)} & "
                f"{_dfmt(float(row['generation_failure_rate']), 2)} & "
                f"{float(row['latency_mean_ms']):.0f} & "
                f"{row['decision']} \\\\"
            )

        lines += [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{adjustbox}",
            (
                r"\caption{Cribado medio cross-model de configuraciones "
                rf"\acro{{RAG}} sobre {_latex_escape(dataset)}. "
                r"\texttt{no\_rag} se conserva como control experimental; "
                r"las configuraciones marcadas como seleccionadas pasan a la "
                r"campaña principal.}"
            ),
            f"\\label{{{_tab_label(FAMILY_MODEL_SELECTION, 'config_screening_cross_model_decision', dataset)}}}",
            r"\end{table}",
            "",
        ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _write_bm25_quality_cost_cross_model_evidence(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    pair_rows: list[dict[str, Any]] = _bm25_faiss_cross_model_pair_rows(
        model_metrics
    )

    if not pair_rows:
        return _write_todo_tex(
            out,
            "no se han encontrado pares BM25/FAISS comparables en los logs "
            "model_selection; regenerar con scripts/generate_charts.py.",
        )

    caption_text: str = (
        r"Evidencia cross-model del compromiso calidad-coste \acro{BM25} "
        r"frente a \acro{FAISS} en "
        f"{_latex_escape(dataset)}."
    )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\small",
        r"\setlength{\tabcolsep}{2pt}",
        r"\renewcommand{\arraystretch}{1.28}",
        r"\begin{adjustbox}{max width=0.96\textwidth}",
        r"\begin{tabular}{lcccccccl}",
        r"\toprule",
        (
            r"\textbf{Par de configuración} & "
            r"\textbf{Puntuación \acro{BM25}} & "
            r"\textbf{Puntuación \acro{FAISS}} & "
            r"\textbf{\abbr{DeltaScore}{$\Delta$\,score}} & "
            r"\textbf{\abbr{LatBM25}{Lat.\,\acro{BM25}} (ms)} & "
            r"\textbf{\abbr{LatFAISS}{Lat.\,\acro{FAISS}} (ms)} & "
            r"\textbf{\abbr{RatioLat}{Ratio\,Lat.}} & "
            r"\textbf{Lectura} \\"
        ),
        r"\midrule",
    ]

    for row in pair_rows:
        pair_label: str = (
            f"\\texttt{{{_latex_escape(row['bm25_cfg'])}}} vs "
            f"\\texttt{{{_latex_escape(row['faiss_cfg'])}}}"
        )

        lines.append(
            f"{pair_label} & "
            f"{_dfmt(float(row['bm25_score']), 2)} & "
            f"{_dfmt(float(row['faiss_score']), 2)} & "
            f"{('+' if float(row['delta_score']) >= 0 else '')}{_dfmt(float(row['delta_score']), 2)} & "
            f"{float(row['bm25_latency']):.0f} & "
            f"{float(row['faiss_latency']):.0f} & "
            f"{_dfmt(float(row['latency_ratio']), 2)}$\\times$ & "
            f"{row['reading']} \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        f"\\caption{{{caption_text}}}",
        f"\\label{{{_tab_label(FAMILY_MODEL_SELECTION, 'bm25_quality_cost_cross_model_evidence', dataset)}}}",
        r"\end{table}",
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _write_bm25_quality_cost_cross_model_interpretation(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    pair_rows: list[dict[str, Any]] = _bm25_faiss_cross_model_pair_rows(
        model_metrics
    )

    bm25_evidence_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "bm25_quality_cost_cross_model_evidence",
        dataset,
    )

    if not pair_rows:
        return _write_todo_tex(
            out,
            "regenerar bm25_quality_cost_cross_model_interpretation.tex cuando "
            "existan pares BM25/FAISS cross-model completos.",
        )

    text: str = (
        f"La Tabla~\\ref{{{bm25_evidence_label}}} muestra que "
        r"las variantes \acro{BM25} no se descartan por ausencia de calidad, "
        r"sino porque su latencia media es muy superior a la de sus pares "
        r"\acro{FAISS} y la mejora de calidad no es estable ni suficiente para "
        r"justificar ese coste."
    )

    out.write_text(text + "\n", encoding="utf-8")
    return out


def _write_config_screening_cross_model_interpretation(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    dataset: str,
    out: Path,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = _cross_model_config_rows(model_metrics)


    if not rows:
        return _write_todo_tex(
            out,
            "regenerar config_screening_cross_model_interpretation.tex con "
            "scripts/generate_charts.py cuando existan logs model_selection.",
        )

    by_config: dict[str, dict[str, Any]] = {
        str(row["config"]): row for row in rows
    }

    config_decision_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "config_screening_cross_model_decision",
        dataset,
    )

    bm25_evidence_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "bm25_quality_cost_cross_model_evidence",
        dataset,
    )

    def _cfg(name: str) -> str:
        return f"\\texttt{{{_latex_escape(name)}}}"

    def _metric(config_name: str, metric_key: str, digits: int = 2) -> str:
        row = by_config.get(config_name)
        if row is None:
            return "--"
        value = row.get(metric_key)
        if not isinstance(value, (int, float)):
            return "--"
        return _dfmt(float(value), digits)

    selected_present: list[str] = [
        cfg for cfg in FINAL_SCREENING_CONFIGS
        if cfg != "no_rag" and cfg in by_config
    ]

    selected_rag_names: str = ", ".join(
        _cfg(cfg) for cfg in selected_present
    )

    baseline_s_score: str = _metric("baseline_s", "score_mean", 2)
    baseline_s_rr_score: str = _metric("baseline_s_rr", "score_mean", 2)
    baseline_s_rr_grounded_score: str = _metric(
        "baseline_s_rr_grounded", "score_mean", 2
    )
    baseline_s_rr_faith: str = _metric(
        "baseline_s_rr", "faithfulness_mean", 2
    )
    baseline_s_rr_grounded_faith: str = _metric(
        "baseline_s_rr_grounded", "faithfulness_mean", 2
    )

    optimized_s_rr_score: str = _metric("optimized_s_rr", "score_mean", 2)
    optimized_s_rr_correctness: str = _metric(
        "optimized_s_rr", "correctness_mean", 2
    )
    optimized_s_rr_global: str = _metric("optimized_s_rr", "overall_mean", 2)
    optimized_s_rr_genfail: str = _metric(
        "optimized_s_rr", "generation_failure_rate", 2
    )

    baseline_s_faith: str = _metric("baseline_s", "faithfulness_mean", 2)
    baseline_s_grounded_faith: str = _metric(
        "baseline_s_grounded", "faithfulness_mean", 2
    )
    baseline_s_correctness: str = _metric("baseline_s", "correctness_mean", 2)
    baseline_s_grounded_correctness: str = _metric(
        "baseline_s_grounded", "correctness_mean", 2
    )
    baseline_s_global: str = _metric("baseline_s", "overall_mean", 2)
    baseline_s_grounded_global: str = _metric(
        "baseline_s_grounded", "overall_mean", 2
    )
    baseline_s_genfail: str = _metric(
        "baseline_s", "generation_failure_rate", 2
    )
    baseline_s_grounded_genfail: str = _metric(
        "baseline_s_grounded", "generation_failure_rate", 2
    )

    optimized_s_grounded_score: str = _metric(
        "optimized_s_grounded", "score_mean", 2
    )

    text_parts: list[str] = [
        (
            f"La Tabla~\\ref{{{config_decision_label}}} resume "
            r"el cribado medio de configuraciones. La puntuación ponderada de cribado se "
            r"calcula según el criterio definido en la "
            r"Sección~\ref{subsec:criterio_agregacion_cribado}: "
            r"$P_{\mathrm{cribado/compuesto}} = "
            r"0.35\cdot\mathrm{Correctness} + "
            r"0.35\cdot\mathrm{Faithfulness} + "
            r"0.20\cdot\mathrm{ContextSupport} + "
            r"0.10\cdot\mathrm{AnswerRelevance}$. "
            r"\texttt{no\_rag} se conserva únicamente como control experimental "
            r"y no se interpreta como una configuración \acro{RAG}. "
            r"El conjunto compacto que pasa a la campaña principal es: "
            f"{selected_rag_names}."
        ),
        (
            r"La selección no equivale a afirmar que todas las configuraciones "
            r"excluidas tengan bajo rendimiento absoluto. La selección reduce "
            r"la campaña principal a las variantes que preservan los contrastes "
            r"necesarios dentro del presupuesto experimental: \texttt{no\_rag} "
            r"frente a \acro{RAG}, \acro{FAISS} sin y con re-ranking, chunking "
            r"fijo frente a chunking semántico, y prompt \texttt{basic} frente "
            r"a \texttt{grounded\_sourced} en las ramas con re-ranking."
        ),
        r"\begin{itemize}",
        (
            rf"\item {_cfg('baseline_s')}: baseline \acro{{FAISS}} con chunking "
            rf"fijo y prompt básico. Se conserva como baseline \acro{{RAG}} "
            rf"principal frente a \texttt{{no\_rag}} y como rama de chunking fijo "
            rf"para comparar contra {_cfg('optimized_s')}."
        ),
        (
            rf"\item {_cfg('baseline_s_rr')}: aísla el efecto del re-ranking "
            rf"sobre chunking fijo. En el cribado cross-model, la puntuación pasa "
            rf"de {baseline_s_score} en {_cfg('baseline_s')} a "
            rf"{baseline_s_rr_score}. Además, permite comparar chunking fijo "
            rf"frente a chunking semántico bajo re-ranking mediante el par "
            rf"{_cfg('baseline_s_rr')} frente a {_cfg('optimized_s_rr')}."
        ),
        (
            rf"\item {_cfg('baseline_s_rr_grounded')}: evalúa el prompt "
            rf"\texttt{{grounded\_sourced}} en la rama con chunking fijo y "
            rf"re-ranking. La puntuación pasa de {baseline_s_rr_score} a "
            rf"{baseline_s_rr_grounded_score} respecto a "
            rf"{_cfg('baseline_s_rr')}, y \emph{{faithfulness}} aumenta de "
            rf"{baseline_s_rr_faith} a {baseline_s_rr_grounded_faith}. También "
            rf"conserva el lado de chunking fijo para comparar contra la variante "
            rf"semántica completa {_cfg('optimized_s_rr_grounded')}."
        ),
        (
            rf"\item {_cfg('optimized_s')}: aísla el chunking semántico sin "
            rf"re-ranking ni prompt grounded. Su función principal es permitir "
            rf"la comparación directa de chunking fijo frente a chunking semántico "
            rf"contra {_cfg('baseline_s')}."
        ),
        (
            rf"\item {_cfg('optimized_s_rr')}: evalúa chunking semántico con "
            rf"re-ranking y prompt básico. Es la configuración con mejor puntuación "
            rf"cross-model en la tabla de cribado ({optimized_s_rr_score}), con "
            rf"corrección {optimized_s_rr_correctness}, puntuación global "
            rf"{optimized_s_rr_global} y tasa de fallo de generación "
            rf"{optimized_s_rr_genfail}\%."
        ),
        (
            rf"\item {_cfg('optimized_s_rr_grounded')}: representa la variante "
            rf"completa \acro{{FAISS}} con chunking semántico, re-ranking y "
            rf"prompt grounded. No se selecciona porque supere necesariamente a "
            rf"{_cfg('optimized_s_rr')}, sino porque permite evaluar la pila "
            rf"completa con grounding y cerrar el contraste contra "
            rf"{_cfg('baseline_s_rr_grounded')}."
        ),
        r"\end{itemize}",
        (
            rf"{_cfg('baseline_s_grounded')} no se descarta por falta de "
            rf"fidelidad: de hecho mejora \emph{{faithfulness}} "
            rf"({baseline_s_grounded_faith} frente a {baseline_s_faith}). "
            rf"Se excluye porque, en la rama sin re-ranking, esa mejora no "
            rf"compensa la pérdida de corrección "
            rf"({baseline_s_correctness} frente a "
            rf"{baseline_s_grounded_correctness}), la caída de puntuación "
            rf"global ({baseline_s_global} frente a "
            rf"{baseline_s_grounded_global}) y el aumento de fallos de "
            rf"generación ({baseline_s_genfail}\% frente a "
            rf"{baseline_s_grounded_genfail}\%). El efecto del prompt "
            rf"\texttt{{grounded\_sourced}} se conserva en la campaña principal "
            rf"mediante las comparaciones con re-ranking, donde la señal "
            rf"experimental es más fuerte."
        ),
        (
            rf"{_cfg('optimized_s_grounded')} se excluye por reducción "
            rf"experimental, no por bajo rendimiento absoluto. Su puntuación es "
            rf"competitiva ({optimized_s_grounded_score}), pero la campaña "
            rf"principal conserva ya los contrastes necesarios sin ejecutar esta "
            rf"variante adicional. En la rama semántica, {_cfg('optimized_s')} "
            rf"mide chunking semántico sin re-ranking, {_cfg('optimized_s_rr')} "
            rf"mide el efecto del re-ranking, y {_cfg('optimized_s_rr_grounded')} "
            rf"mide la variante completa con re-ranking y grounding. Además, el "
            rf"contraste entre chunking fijo y chunking semántico no se pierde: "
            rf"queda representado por los pares {_cfg('baseline_s')} frente a "
            rf"{_cfg('optimized_s')}, {_cfg('baseline_s_rr')} frente a "
            rf"{_cfg('optimized_s_rr')}, y {_cfg('baseline_s_rr_grounded')} "
            rf"frente a {_cfg('optimized_s_rr_grounded')}. Por tanto, "
            rf"{_cfg('optimized_s_grounded')} queda como evidencia secundaria del "
            rf"cribado medio, no como configuración final."
        ),
        (
            r"Las variantes \acro{BM25} se excluyen por criterio calidad-coste; "
            r"la evidencia específica se recoge en la "
            f"Tabla~\\ref{{{bm25_evidence_label}}}."
        ),
    ]

    out.write_text("\n\n".join(text_parts) + "\n", encoding="utf-8")
    return out


def _write_todo_tex(path: Path, message: str) -> Path:

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"% TODO: {message}\n", encoding="utf-8")
    return path


def _write_thesis_compact_artifacts(
    family: str,
    dataset: str,
    model: str,
    metrics: dict[str, dict[str, float]],
    thesis_dir: Path,
) -> list[Path]:

    import warnings

    warnings.warn(
        "_write_thesis_compact_artifacts is deprecated; use "
        "write_group_thesis_artifacts or write_cross_model_thesis_artifacts.",
        DeprecationWarning,
        stacklevel=2,
    )
    thesis_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    if family == FAMILY_MODEL_SELECTION:
        generated.append(_write_config_screening_decision(
            metrics, thesis_dir / "config_screening_decision.tex",
            dataset=dataset, model=model,
        ))
        generated.append(_write_config_screening_interpretation(
            metrics,
            thesis_dir / "config_screening_interpretation.tex",
            dataset=dataset,
            model=model,
        ))
        generated.append(_write_bm25_quality_cost_evidence(
            metrics, thesis_dir / "bm25_quality_cost_evidence.tex",
            dataset=dataset, model=model,
        ))
        generated.append(_write_bm25_interpretation(
            thesis_dir / "bm25_interpretation.tex",
        ))
    elif family == FAMILY_MAIN_EXPERIMENT:
        generated.append(_write_final_results_table(
            metrics, thesis_dir / "final_results_table.tex",
            dataset=dataset, model=model,
        ))
        generated.append(_write_final_results_interpretation(
            metrics, thesis_dir / "final_results_interpretation.tex",
            dataset=dataset, model=model,
        ))

    return generated


def _classify_screening_configs(
    metrics: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:


    SCORE_BAND: float = 2.0
    LATENCY_RATIO_CAP: float = 1.40

    rag_rows: list[tuple[str, float, float]] = []
    control_row: tuple[str, float, float] | None = None
    for name, m in metrics.items():
        entry: tuple[str, float, float] = (
            name,
            _thesis_quality_score(m),
            float(m.get("latency_mean_ms", 0.0)),
        )
        if name == "no_rag":
            control_row = entry
        else:
            rag_rows.append(entry)


    rag_rows.sort(key=lambda r: (-r[1], r[2]))
    best_score: float = rag_rows[0][1] if rag_rows else 0.0


    in_band: list[tuple[str, float, float]] = [
        r for r in rag_rows if (best_score - r[1]) <= SCORE_BAND
    ]
    best_latency: float = (
        min((r[2] for r in in_band if r[2] > 0.0), default=0.0)
        if in_band
        else 0.0
    )

    result: list[dict[str, Any]] = []


    if control_row is not None:
        result.append({
            "name": control_row[0],
            "score": control_row[1],
            "latency": control_row[2],
            "role": "control",
            "decision": "Control (no excluible).",
        })

    for name, score, latency in rag_rows:
        gap: float = best_score - score
        latency_ratio: float = (
            (latency / best_latency) if best_latency > 0.0 else 1.0
        )
        role: str
        decision: str
        if gap <= SCORE_BAND and latency_ratio <= LATENCY_RATIO_CAP:
            role = "selected"
            if name == rag_rows[0][0]:
                decision = "Seleccionada (mejor del cribado)."
            else:
                decision = "Seleccionada."
        elif gap <= SCORE_BAND and latency_ratio > LATENCY_RATIO_CAP:
            role = "discarded"
            decision = (
                f"Excluida: latencia {_dfmt(latency_ratio, 2)}\\,$\\times$ "
                f"sin ganancia de calidad."
            )
        else:
            role = "discarded"
            decision = f"Excluida: gap de {_dfmt(gap, 2)}\\,pts de calidad."
        result.append({
            "name": name,
            "score": score,
            "latency": latency,
            "role": role,
            "decision": decision,
        })

    return result


def _write_config_screening_decision(
    metrics: dict[str, dict[str, float]],
    out: Path,
    dataset: str,
    model: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        return _write_todo_tex(
            out,
            "regenerar config_screening_decision.tex con scripts/generate_charts.py "
            "cuando existan logs del cribado medio.",
        )

    rows: list[dict[str, Any]] = _classify_screening_configs(metrics)

    decision_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "config_screening_decision",
        dataset,
        model,
    )
    caption_text: str = (
        f"Cribado medio de configuraciones \\acro{{RAG}} sobre "
        f"{_latex_escape(dataset)} ({_latex_escape(model)}). "
        r"\texttt{no\_rag} se conserva siempre como control experimental; "
        r"las configuraciones marcadas como seleccionadas pasan a la campaña principal."
    )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{adjustbox}{max width=0.96\textwidth}",
        r"\begin{tabular}{lrrl}",
        r"\toprule",
        (
            r"\textbf{Configuración} & "
            r"\textbf{Puntuación ponderada} & "
            r"\textbf{Latencia media (ms)} & "
            r"\textbf{Decisión} \\"
        ),
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"\\texttt{{{_latex_escape(row['name'])}}} & "
            f"{_dfmt(row['score'], 2)} & {row['latency']:.0f} & "
            f"{row['decision']} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{decision_label}}}",
        r"\end{table}",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _write_config_screening_interpretation(
    metrics: dict[str, dict[str, float]],
    out: Path,
    dataset: str,
    model: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        return _write_todo_tex(
            out,
            "regenerar config_screening_interpretation.tex con scripts/generate_charts.py "
            "cuando existan logs del cribado medio.",
        )

    rows: list[dict[str, Any]] = _classify_screening_configs(metrics)
    if not rows:
        return _write_todo_tex(out, "no hay métricas para interpretar.")

    selected: list[dict[str, Any]] = [r for r in rows if r["role"] == "selected"]
    discarded: list[dict[str, Any]] = [r for r in rows if r["role"] == "discarded"]
    has_control: bool = any(r["role"] == "control" for r in rows)

    decision_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "config_screening_decision",
        dataset,
        model,
    )

    selected_names: str = ", ".join(
        f"\\texttt{{{_latex_escape(r['name'])}}}" for r in selected
    ) or "(ninguna)"

    text_parts: list[str] = []
    text_parts.append(
        f"La Tabla~\\ref{{{decision_label}}} resume el cribado medio "
        r"de configuraciones \acro{RAG} sobre la combinación retriever/re-ranker "
        r"seleccionada en la fase preliminar. "
    )
    if has_control:
        text_parts.append(
            r"La fila \texttt{no\_rag} se conserva siempre como control experimental "
            r"y queda excluida del descarte. "
        )
    text_parts.append(
        f"Pasan a la campaña principal {len(selected)} "
        f"configuracion{'es' if len(selected) != 1 else ''} " + r"\acro{RAG}: "
        f"{selected_names}. "
    )

    if discarded:

        worst: list[dict[str, Any]] = sorted(
            discarded, key=lambda r: r["score"]
        )[:2]
        reasons: str = "; ".join(
            f"\\texttt{{{_latex_escape(r['name'])}}} ({r['decision'].rstrip('.').lower()})"
            for r in worst
        )
        text_parts.append(
            f"Se descartan {len(discarded)} "
            f"configuracion{'es' if len(discarded) != 1 else ''} mediante "
            r"\texttt{DISABLED\_CONFIGS}: "
            f"{reasons}. "
        )
    text_parts.append(
        r"La interpretación detallada de cada descarte se desarrolla en el "
        r"Capítulo~\ref{ch:discusion}."
    )

    out.write_text("".join(text_parts) + "\n", encoding="utf-8")
    return out


def _write_bm25_quality_cost_evidence(
    metrics: dict[str, dict[str, float]],
    out: Path,
    dataset: str,
    model: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        return _write_todo_tex(
            out,
            "regenerar bm25_quality_cost_evidence.tex con scripts/generate_charts.py "
            "cuando existan logs del cribado medio.",
        )


    pairs: list[tuple[str, str]] = []
    for name in metrics:
        if not name.endswith(name):
            continue
        if "_k" in name and "_s" not in name:
            faiss_name = name.replace("_k", "_s", 1)
            if faiss_name in metrics and (name, faiss_name) not in pairs:
                pairs.append((name, faiss_name))

    if not pairs:
        return _write_todo_tex(
            out,
            "no se han encontrado pares \\acro{BM25}/\\acro{FAISS} comparables en los "
            "logs disponibles; ejecutar el cribado medio antes de regenerar.",
        )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{adjustbox}{max width=0.96\textwidth}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        (
            r"\textbf{Par de configuración} & "
            r"\textbf{Puntuación \acro{BM25}} & "
            r"\textbf{Puntuación \acro{FAISS}} & "
            r"\textbf{\abbr{LatBM25}{Lat.\,\acro{BM25}} (ms)} & "
            r"\textbf{\abbr{LatFAISS}{Lat.\,\acro{FAISS}} (ms)} \\"
        ),
        r"\midrule",
    ]
    for bm25_name, faiss_name in pairs:
        bm: dict[str, float] = metrics[bm25_name]
        fa: dict[str, float] = metrics[faiss_name]
        lines.append(
            f"\\texttt{{{_latex_escape(bm25_name)}}} vs "
            f"\\texttt{{{_latex_escape(faiss_name)}}} & "
            f"{_dfmt(_thesis_quality_score(bm), 2)} & "
            f"{_dfmt(_thesis_quality_score(fa), 2)} & "
            f"{float(bm.get('latency_mean_ms', 0.0)):.0f} & "
            f"{float(fa.get('latency_mean_ms', 0.0)):.0f} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        (
            r"\caption{Evidencia calidad-coste \acro{BM25} frente a \acro{FAISS} en "
            f"{_latex_escape(dataset)} con modelo "
            f"\\texttt{{{_latex_escape(model)}}}.}}"
        ),
        f"\\label{{{_tab_label(FAMILY_MODEL_SELECTION, 'bm25_quality_cost_evidence', dataset, model)}}}",
        r"\end{table}",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _write_bm25_interpretation(out: Path) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)
    text: str = (
        r"Los resultados no permiten descartar \acro{BM25} por baja calidad "
        r"absoluta. En algunas configuraciones, especialmente cuando se combina "
        r"con prompt \texttt{grounded\_sourced}, \acro{BM25} alcanza valores "
        r"competitivos de corrección y fidelidad. Sin embargo, el criterio de "
        r"selección del proyecto no considera solo calidad, sino también coste "
        r"temporal. En Trivia\acro{QA}, las variantes \acro{BM25} presentan "
        r"latencias de recuperación muy superiores a las variantes \acro{FAISS}, "
        r"mientras que la mejora de calidad no es suficientemente estable para "
        r"compensar ese coste. Por tanto, \acro{BM25} se conserva como baseline "
        r"léxico y como evidencia del compromiso calidad-latencia, pero no se "
        r"selecciona como configuración final."
    )
    out.write_text(text + "\n", encoding="utf-8")
    return out


def _write_final_results_table(
    metrics: dict[str, dict[str, float]],
    out: Path,
    dataset: str,
    model: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        return _write_todo_tex(
            out,
            "regenerar final_results_table.tex con scripts/generate_charts.py "
            "cuando existan logs de la campaña principal.",
        )

    rows: list[tuple[str, dict[str, float]]] = [
        (name, m) for name, m in metrics.items()
    ]
    rows.sort(key=lambda r: -_thesis_quality_score(r[1]))

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{adjustbox}{max width=1.0\textwidth}",
        r"\begin{tabular}{lccccccr}",
        r"\toprule",
        (
            r"\textbf{Configuración} & "
            r"\textbf{\abbr{Correct}{Correctness\textsuperscript{c}}} & "
            r"\textbf{\abbr{Faith}{Faithfulness\textsuperscript{c}}} & "
            r"\textbf{\abbr{AnsRel}{AnsRel.\textsuperscript{c}}} & "
            r"\textbf{\abbr{CtxSup}{Ctx. Support\textsuperscript{c}}} & "
            r"\textbf{\abbr{Global}{Global\textsuperscript{c}}} & "
            r"\textbf{Puntuación compuesta$^*$} & "
            r"\textbf{\abbr{Lat}{Latencia (ms)}} \\"
        ),
        r"\midrule",
    ]
    for name, m in rows:
        composite: float = _thesis_quality_score(m)
        lines.append(
            f"\\texttt{{{_latex_escape(name)}}} & "
            f"{_dfmt(float(m.get('correctness_mean', 0.0)), 2)} & "
            f"{_dfmt(float(m.get('faithfulness_mean', 0.0)), 2)} & "
            f"{_dfmt(float(m.get('answer_relevance_mean', 0.0)), 2)} & "
            f"{_dfmt(float(m.get('context_support_mean', 0.0)), 2)} & "
            f"{_dfmt(float(m.get('overall_mean', 0.0)), 2)} & "
            f"{_dfmt(composite, 2)} & "
            f"{float(m.get('latency_mean_ms', 0.0)):.0f} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        (
            r"\caption{Resultados finales de la campaña principal sobre "
            f"{_latex_escape(dataset)} con modelo el "
            f"\\texttt{{{_latex_escape(model)}}}.}}"
        ),
        f"\\label{{{_tab_label(FAMILY_MAIN_EXPERIMENT, 'final_results', dataset, model)}}}",
        (
            r"\par\smallskip"
            r"{\scriptsize $^*$Compuesto "
            r"$= ((0{,}35\cdot\text{Correctness}) + (0{,}35\cdot\text{Faithfulness}) "
            r"+ (0{,}20\cdot\text{Context support}) + (0{,}10\cdot\text{Answer relevance}$)); "
            r"criterio de ordenación de filas.}"
        ),
        r"\end{table}",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _write_final_results_interpretation(
    metrics: dict[str, dict[str, float]],
    out: Path,
    dataset: str,
    model: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        return _write_todo_tex(
            out,
            "regenerar final_results_interpretation.tex con scripts/generate_charts.py "
            "cuando existan logs de la campaña principal.",
        )

    rows: list[tuple[str, float, float]] = sorted(
        (
            (name, _thesis_quality_score(m), float(m.get("latency_mean_ms", 0.0)))
            for name, m in metrics.items()
        ),
        key=lambda r: -r[1],
    )

    final_results_label: str = _tab_label(
        FAMILY_MAIN_EXPERIMENT,
        "final_results",
        dataset,
        model,
    )

    if not rows:
        return _write_todo_tex(out, "no hay métricas para interpretar.")

    top_name, top_score, top_lat = rows[0]
    text: str = (
        f"La Tabla~\\ref{{{final_results_label}}} muestra los resultados de la campaña "
        r"principal sobre las configuraciones supervivientes al cribado medio. "
        f"La configuración \\texttt{{{_latex_escape(top_name)}}} obtiene la "
        f"mayor puntuación ponderada ({_dfmt(top_score, 2)}) con una latencia "
        f"media de {top_lat:.0f}\\,ms. La interpretación cualitativa de estos "
        r"resultados, junto con las limitaciones del experimento, se desarrolla "
        r"en el Capítulo~\ref{ch:discusion}."
    )
    out.write_text(text + "\n", encoding="utf-8")
    return out


def _write_model_selection_interpretation(
    model_metrics: dict[str, dict[str, dict[str, float]]],
    out: Path,
    dataset: str,
) -> Path:

    out.parent.mkdir(parents=True, exist_ok=True)

    ranking: list[dict[str, Any]] = _rank_models_for_cross_model_selection(
        model_metrics
    )

    if not ranking:
        return _write_todo_tex(
            out,
            "regenerar model_selection_interpretation.tex con scripts/generate_charts.py "
            "cuando existan los logs cross-model de model_selection.",
        )

    by_model: dict[str, dict[str, Any]] = {
        str(row["model"]): row for row in ranking
    }

    selected: list[dict[str, Any]] = [
        by_model[name]
        for name in FINAL_SELECTED_GENERATOR_MODELS
        if name in by_model
    ]

    discarded: list[dict[str, Any]] = [
        by_model[name]
        for name in FINAL_DISCARDED_GENERATOR_MODELS
        if name in by_model
    ]

    if not selected:
        return _write_todo_tex(
            out,
            "no hay modelos seleccionados presentes en los logs; revisar "
            "FINAL_SELECTED_GENERATOR_MODELS o los nombres detectados de modelo.",
        )

    model_decision_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "model_decision",
        dataset,
    )

    detailed_table_label: str = _tab_label(
        FAMILY_MODEL_SELECTION,
        "cross_model",
        dataset,
    )

    def _model(row: dict[str, Any]) -> str:
        return f"\\texttt{{{_latex_escape(row['model'])}}}"

    def _selected_fragment(row: dict[str, Any]) -> str:
        return (
            f"{_model(row)} "
            f"({_dfmt(float(row['score_mean']), 2)} puntos; "
            f"{float(row['latency_mean_ms']):.0f}\\,ms)"
        )

    selected_sorted: list[dict[str, Any]] = sorted(
        selected,
        key=lambda row: -float(row["score_mean"]),
    )

    if len(selected_sorted) == 1:
        selected_text = _selected_fragment(selected_sorted[0])
    else:
        selected_text = (
            ", ".join(_selected_fragment(row).replace(".", ",") for row in selected_sorted[:-1])
            + " y "
            + _selected_fragment(selected_sorted[-1]).replace(".", ",")
        )


    selection_threshold: dict[str, Any] = min(
        selected_sorted,
        key=lambda row: float(row["score_mean"]),
    )

    def _discard_sentence(row: dict[str, Any]) -> str:
        score_gap = str(round(
            (float(selection_threshold["score_mean"])
            - float(row["score_mean"])
        ), 2)).replace(".", ",")
        latency_delta: float = (
            float(row["latency_mean_ms"])
            - float(selection_threshold["latency_mean_ms"])
        )

        if abs(latency_delta) < 50.0:
            latency_clause = (
                r"con una latencia media similar a la del modelo seleccionado "
                r"más cercano"
            )
        elif latency_delta > 0:
            latency_clause = (
                f"con una latencia media {latency_delta:.0f}\\,ms superior "
                r"a la del modelo seleccionado más cercano"
            )
        else:
            latency_clause = (
                f"aunque su latencia media es {-latency_delta:.0f}\\,ms inferior "
                r"a la del modelo seleccionado más cercano"
            )

        return (
            f"{_model(row)} se descarta para la campaña principal porque su "
            f"puntuación media ({str(round(float(row['score_mean']), 2)).replace(".", ",")}) queda "
            f"{score_gap} puntos por debajo del umbral marcado por "
            f"{_model(selection_threshold)} "
            f"({str(round(float(selection_threshold['score_mean']), 2)).replace(".", ",")}). "
            f"{latency_clause.capitalize()}, esa reducción de latencia no "
            r"compensa la pérdida de calidad observada en el cribado medio."
        )

    if discarded:
        discarded_text = " ".join(_discard_sentence(row) for row in discarded)
    else:
        discarded_text = (
            r"No se descarta ningún modelo generativo porque todos los modelos "
            r"con métricas válidas forman parte del conjunto seleccionado."
        )

    selected_pair_text = ""
    if len(selected_sorted) >= 2:
        best_selected: dict[str, Any] = selected_sorted[0]
        second_selected: dict[str, Any] = selected_sorted[1]

        selected_gap = str(round((
            float(best_selected["score_mean"])
            - float(second_selected["score_mean"])
        ), 2)).replace(".", ",")
        selected_latency_delta: float = (
            float(second_selected["latency_mean_ms"])
            - float(best_selected["latency_mean_ms"])
        )

        if selected_latency_delta < 0:
            latency_phrase = (
                f"y además presenta una latencia media "
                f"{-selected_latency_delta:.0f}\\,ms inferior"
            )
        elif selected_latency_delta > 0:
            latency_phrase = (
                f"aunque presenta una latencia media "
                f"{selected_latency_delta:.0f}\\,ms superior"
            )
        else:
            latency_phrase = r"con latencia media equivalente"

        selected_pair_text = (
            f"La diferencia entre {_model(best_selected)} y "
            f"{_model(second_selected)} es reducida "
            f"({selected_gap} puntos de media), {latency_phrase}; "
            f"por ello, {_model(second_selected)} se conserva para la campaña "
            r"principal y no se interpreta como modelo descartado. "
        )

    text: str = (
        f"La Tabla~\\ref{{{model_decision_label}}} documenta la selección "
        r"cross-model de modelos generativos para la campaña principal. La "
        r"evidencia detallada por modelo y configuración queda recogida en la "
        f"Tabla~\\ref{{{detailed_table_label}}}. "
        r"El cribado se calcula sobre el conjunto compacto de configuraciones "
        r"\acro{RAG} seleccionadas y excluye \texttt{no\_rag}, porque "
        r"\texttt{no\_rag} es un control experimental y no una configuración "
        r"\acro{RAG}. "
        f"Los modelos conservados para la campaña principal son {selected_text}. "
        f"{selected_pair_text}"
        f"{discarded_text} "
        r"Esta decisión es instrumental: reduce el coste de la campaña final "
        r"sin presentar el cribado medio como una comparación general y "
        r"definitiva entre modelos generativos."
    )

    out.write_text(text + "\n", encoding="utf-8")
    return out


def write_budget_table(out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)

    items = _budget_items()

    imputed_total = sum(
        (item.amount for item in items if item.include_in_imputed_total),
        Decimal("0"),
    )
    direct_total = sum(
        (item.amount for item in items if item.include_in_direct_total),
        Decimal("0"),
    )
    direct_total_is_approximate = any(
        item.approximate for item in items if item.include_in_direct_total
    )

    lines: list[str] = [
        r"\begin{table}[H]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.05}",
        r"\begin{adjustbox}{max width=\textwidth}",
        r"\begin{tabular}{p{0.27\textwidth}rp{0.50\textwidth}}",
        r"\toprule",
        r"\textbf{Concepto} & \textbf{Coste} & \textbf{Descripción} \\",
        r"\midrule",
    ]

    for item in items:
        lines.append(
            f"{item.concept} & "
            f"{_format_eur(item.amount, item.approximate, item.qualifier)} & "
            f"{item.description} \\\\"
        )
        lines.append(r"\midrule")

    lines.extend([
        r"\textbf{Total estimado imputado} & "
        f"$\\approx$\\textbf{{{_format_eur(imputed_total)}}} & "
        f"El coste directo estimado del proyecto es "
        f"{_format_eur(direct_total, approximate=direct_total_is_approximate)}. "
        r"El coste imputado refleja el valor del trabajo y de los recursos "
        r"utilizados. \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        r"\caption{Presupuesto estimado del proyecto.}",
        r"\label{tab:presupuesto_proyecto}",
        r"\end{table}",
        "",
    ])

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_budget_macros(output_path: Path) -> Path:
    items = _budget_items()

    llm_judge = _budget_item_by_concept(
        items,
        "Evaluación externa con \\acro{LLM} juez",
    )

    imputed_total = _budget_imputed_total(items)
    direct_total = _budget_direct_total(items)

    lines = [
        "% Archivo generado automáticamente. No editar a mano.",
        f"\\newcommand{{\\BudgetLLMJudgeCost}}{{{_format_eur(llm_judge.amount, llm_judge.approximate)}}}",
        f"\\newcommand{{\\BudgetLLMJudgeCostText}}{{{_format_eur_prose(llm_judge.amount, llm_judge.approximate)}}}",
        f"\\newcommand{{\\BudgetDirectTotal}}{{{_format_eur(direct_total)}}}",
        f"\\newcommand{{\\BudgetImputedTotal}}{{{_format_eur(imputed_total)}}}",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_group_thesis_artifacts(
    family: str,
    dataset: str,
    model: str,
    metrics: dict[str, dict[str, float]],
    thesis_dir: Path,
) -> list[Path]:

    generated: list[Path] = []
    if family == FAMILY_MODEL_SELECTION:
        generated.append(_write_config_screening_decision(
            metrics,
            thesis_dir / "config_screening_decision.tex",
            dataset=dataset,
            model=model,
        ))
        generated.append(_write_config_screening_interpretation(
            metrics,
            thesis_dir / "config_screening_interpretation.tex",
            dataset=dataset,
            model=model,
        ))
        generated.append(_write_bm25_quality_cost_evidence(
            metrics,
            thesis_dir / "bm25_quality_cost_evidence.tex",
            dataset=dataset,
            model=model,
        ))
        generated.append(_write_bm25_interpretation(
            thesis_dir / "bm25_interpretation.tex",
        ))
    elif family == FAMILY_MAIN_EXPERIMENT:
        generated.append(_write_final_results_table(
            metrics,
            thesis_dir / "final_results_table.tex",
            dataset=dataset,
            model=model,
        ))
        generated.append(_write_final_results_interpretation(
            metrics,
            thesis_dir / "final_results_interpretation.tex",
            dataset=dataset,
            model=model,
        ))
    return generated
def write_cross_model_thesis_artifacts(
    family: str,
    dataset: str,
    model_metrics: dict[str, dict[str, dict[str, float]]],
    cross_dir: Path,
) -> list[Path]:

    generated: list[Path] = []

    if family != FAMILY_MODEL_SELECTION:
        return generated
    generated.append(_write_model_selection_decision(
        model_metrics=model_metrics,
        dataset=dataset,
        out=cross_dir / "model_selection_decision.tex",
    ))
    generated.append(_write_model_selection_interpretation(
        model_metrics=model_metrics,
        out=cross_dir / "model_selection_interpretation.tex",
        dataset=dataset,
    ))
    generated.append(_write_config_screening_cross_model_decision(
        model_metrics=model_metrics,
        dataset=dataset,
        out=cross_dir / "config_screening_cross_model_decision.tex",
    ))
    generated.append(_write_config_screening_cross_model_interpretation(
        model_metrics=model_metrics,
        dataset=dataset,
        out=cross_dir / "config_screening_cross_model_interpretation.tex",
    ))
    generated.append(_write_bm25_quality_cost_cross_model_evidence(
        model_metrics=model_metrics,
        dataset=dataset,
        out=cross_dir / "bm25_quality_cost_cross_model_evidence.tex",
    ))
    generated.append(_write_bm25_quality_cost_cross_model_interpretation(
        model_metrics=model_metrics,
        dataset=dataset,
        out=cross_dir / "bm25_quality_cost_cross_model_interpretation.tex",
    ))
    return generated
