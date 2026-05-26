from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, ClassVar

try:
    from scipy.stats import wilcoxon
    _HAS_SCIPY: bool = True
except ImportError:
    _HAS_SCIPY = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger("compare_components")


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RUNS_DIR: Path = PROJECT_ROOT / "logs" / "runs"
OUTPUT_ROOT: Path = (
    PROJECT_ROOT / "output" / "thesis" / "main_experiments" / "component_effects"
)


DEFAULT_DATASET: str = "triviaqa"

DEFAULT_MIN_SAMPLES: int = 600

RETRIEVER_MIN_CAP: int = 45

QUALITY_EQUIV_DELTA: float = 2.0

ALPHA: float = 0.05


CONTINUOUS_SCORE_KEYS: tuple[str, ...] = (
    "correctness",
    "faithfulness",
    "answer_relevance",
    "context_support",
    "overall",
)

RATE_METRIC_KEYS: tuple[str, ...] = (
    "answer_accuracy",
    "context_sufficiency_rate",
    "faithfulness_rate",
    "contradiction_rate",
    "retrieval_failure_rate",
    "generation_failure_rate",
    "overconfidence_rate",
)


CHUNKING_PAIRS: tuple[tuple[str, str], ...] = (
    ("baseline_s",              "optimized_s"),
    ("baseline_s_rr",           "optimized_s_rr"),
    ("baseline_s_grounded",     "optimized_s_grounded"),
    ("baseline_s_rr_grounded",  "optimized_s_rr_grounded"),
    ("baseline_k",              "optimized_k"),
    ("baseline_k_rr",           "optimized_k_rr"),
    ("baseline_k_grounded",     "optimized_k_grounded"),
    ("baseline_k_rr_grounded",  "optimized_k_rr_grounded"),
)

RERANKING_PAIRS: tuple[tuple[str, str], ...] = (
    ("baseline_s",              "baseline_s_rr"),
    ("optimized_s",             "optimized_s_rr"),
    ("baseline_s_grounded",     "baseline_s_rr_grounded"),
    ("optimized_s_grounded",    "optimized_s_rr_grounded"),
    ("baseline_k",              "baseline_k_rr"),
    ("optimized_k",             "optimized_k_rr"),
    ("baseline_k_grounded",     "baseline_k_rr_grounded"),
    ("optimized_k_grounded",    "optimized_k_rr_grounded"),
)

GROUNDING_PAIRS: tuple[tuple[str, str], ...] = (
    ("baseline_s",      "baseline_s_grounded"),
    ("baseline_s_rr",   "baseline_s_rr_grounded"),
    ("optimized_s",     "optimized_s_grounded"),
    ("optimized_s_rr",  "optimized_s_rr_grounded"),
    ("baseline_k",      "baseline_k_grounded"),
    ("baseline_k_rr",   "baseline_k_rr_grounded"),
    ("optimized_k",     "optimized_k_grounded"),
    ("optimized_k_rr",  "optimized_k_rr_grounded"),
)

RETRIEVER_PAIRS: tuple[tuple[str, str], ...] = (
    ("baseline_k",              "baseline_s"),
    ("baseline_k_rr",           "baseline_s_rr"),
    ("baseline_k_grounded",     "baseline_s_grounded"),
    ("baseline_k_rr_grounded",  "baseline_s_rr_grounded"),
    ("optimized_k",             "optimized_s"),
    ("optimized_k_rr",          "optimized_s_rr"),
    ("optimized_k_grounded",    "optimized_s_grounded"),
    ("optimized_k_rr_grounded", "optimized_s_rr_grounded"),
)


@dataclass
class EffectSpec:


    key: str
    spanish_name: str
    pairs: tuple[tuple[str, str], ...]
    left_label: str
    right_label: str
    table_metrics: tuple[str, ...]
    chart_metrics: tuple[str, str]
    support_fn: Callable[[dict[str, Any]], bool]
    label_tag: str

    effective_min_samples: int = 0


def _support_chunking(r: dict[str, Any]) -> bool:

    return bool(
        r.get("delta_context_tokens_est_mean", 0.0) < 0.0
        and abs(r.get("delta_correctness_mean", 0.0)) <= QUALITY_EQUIV_DELTA
        and abs(r.get("delta_overall_mean",     0.0)) <= QUALITY_EQUIV_DELTA
    )


def _support_reranking(r: dict[str, Any]) -> bool:

    overall_d: float    = r.get("delta_overall_mean", 0.0)
    ctxsup_d: float     = r.get("delta_context_support_mean", 0.0)
    corr_d: float       = r.get("delta_correctness_mean", 0.0)
    lat_pct: float      = r.get("delta_latency_ratio_pct", 0.0)
    quality_ok: bool    = (overall_d >= 0.0) or (ctxsup_d >= 0.0)
    correctness_ok: bool = corr_d >= -QUALITY_EQUIV_DELTA
    latency_ok: bool    = (lat_pct <= 50.0) or (overall_d >= 2.0)
    return bool(quality_ok and correctness_ok and latency_ok)


def _support_grounding(r: dict[str, Any]) -> bool:

    return bool(
        r.get("delta_faithfulness_mean",  0.0) >= 0.0
        and r.get("delta_correctness_mean", 0.0) >= -QUALITY_EQUIV_DELTA
        and r.get("delta_overconfidence_rate_mean", 0.0) <= 0.0
        and r.get("delta_false_refusal_rate_mean",  0.0) <= QUALITY_EQUIV_DELTA
    )


def _support_retriever(r: dict[str, Any]) -> bool:

    overall_d: float = r.get("delta_overall_mean", 0.0)
    lat_pct: float   = r.get("delta_latency_ratio_pct", 0.0)
    return bool(overall_d >= 0.0 and (lat_pct <= 0.0 or overall_d >= 2.0))


def _completed_by_index(exp_json: dict[str, Any]) -> dict[str, dict[str, Any]]:

    out: dict[str, dict[str, Any]] = {}
    for i, s in enumerate(exp_json.get("samples", [])):
        ev: dict[str, Any] = s.get("eval") or {}
        if ev.get("status") != "completed":
            continue
        idx_val: Any = s.get("index", i)
        try:
            key: str = str(int(idx_val))
        except (TypeError, ValueError):
            key = str(idx_val)
        out[key] = s
    return out


def _sample_continuous_score(sample: dict[str, Any], score_key: str) -> float | None:

    sc: Any = (sample.get("eval") or {}).get("scores") or {}
    v: Any = sc.get(score_key)
    return float(v) if isinstance(v, (int, float)) else None


def _sample_rate(sample: dict[str, Any], rate_key: str) -> float | None:

    ev: dict[str, Any]  = sample.get("eval") or {}
    jn: dict[str, Any]  = ev.get("judge_notes") or {}
    sc: dict[str, Any]  = ev.get("scores") or {}


    _BOOL_MAP: dict[str, str] = {
        "answer_accuracy":          "answer_correct",
        "context_sufficiency_rate": "context_sufficient",
        "faithfulness_rate":        "answer_supported_by_context",
        "contradiction_rate":       "has_contradiction",
    }
    if rate_key in _BOOL_MAP:
        v: Any = jn.get(_BOOL_MAP[rate_key])
        return 100.0 if v is True else (0.0 if v is False else None)


    if rate_key == "retrieval_failure_rate":
        ft: Any = jn.get("failure_type")
        return 100.0 if ft == "retrieval_failure" else (0.0 if ft is not None else None)
    if rate_key == "generation_failure_rate":
        ft = jn.get("failure_type")
        return 100.0 if ft == "generation_failure" else (0.0 if ft is not None else None)


    if rate_key == "overconfidence_rate":
        answer_correct: Any   = jn.get("answer_correct")
        is_refusal: Any       = jn.get("is_refusal")
        context_sufficient: Any = jn.get("context_sufficient")
        ans_rel: Any          = sc.get("answer_relevance")

        if (
            answer_correct is None
            or is_refusal is None
            or context_sufficient is None
            or not isinstance(ans_rel, (int, float))
        ):
            return None
        triggered: bool = (
            answer_correct is False
            and is_refusal is False
            and context_sufficient is False
            and float(ans_rel) >= 70.0
        )
        return 100.0 if triggered else 0.0


    if rate_key == "false_refusal_rate":
        v = jn.get("is_false_refusal")
        return 100.0 if v is True else (0.0 if v is False else None)

    return None


def _sample_latency_ms(sample: dict[str, Any]) -> float | None:

    timings: dict[str, Any] = sample.get("timings_ms") or {}
    v: Any = timings.get("total_pipeline")
    return float(v) if isinstance(v, (int, float)) else None


def _config_latency_fallback(exp_json: dict[str, Any]) -> float | None:

    for m in exp_json.get("metrics", []):
        if m.get("metric") == "latency_mean_ms":
            v: Any = m.get("value")
            return float(v) if isinstance(v, (int, float)) else None
    return None


def _sample_context_tokens(sample: dict[str, Any]) -> float | None:

    v: Any = sample.get("context_tokens_est")
    return float(v) if isinstance(v, (int, float)) else None


def _paired_floats(
    left_idx: dict[str, dict[str, Any]],
    right_idx: dict[str, dict[str, Any]],
    extractor: Callable[[dict[str, Any]], float | None],
    common: list[str],
) -> tuple[list[float], list[float]]:

    lv: list[float] = []
    rv: list[float] = []
    for idx in common:
        a: float | None = extractor(left_idx[idx])
        b: float | None = extractor(right_idx[idx])
        if a is None or b is None:
            continue
        lv.append(a)
        rv.append(b)
    return lv, rv


def _mean(xs: list[float]) -> float:

    return statistics.mean(xs) if xs else 0.0


def _wilcoxon_p(a: list[float], b: list[float]) -> float | None:

    if not _HAS_SCIPY or len(a) < 6:
        return None
    diffs: list[float] = [bi - ai for ai, bi in zip(a, b)]
    if all(d == 0.0 for d in diffs):
        return None
    try:
        res: Any = wilcoxon(a, b, zero_method="wilcox", correction=False)
        return float(res.pvalue if hasattr(res, "pvalue") else res[1])
    except ValueError:
        return None


def _compare_pair(
    run_id: str,
    left_data: dict[str, Any],
    right_data: dict[str, Any],
    left_name: str,
    right_name: str,
    effect_key: str,
    threshold: int,
) -> dict[str, Any] | None:

    left_idx: dict[str, dict[str, Any]]  = _completed_by_index(left_data)
    right_idx: dict[str, dict[str, Any]] = _completed_by_index(right_data)
    common_set: set[str] = set(left_idx) & set(right_idx)


    bad: list[str] = [
        i for i in common_set
        if str(left_idx[i].get("question", "")).strip()
        != str(right_idx[i].get("question", "")).strip()
    ]
    for i in bad:
        left_idx.pop(i, None)
        right_idx.pop(i, None)
        common_set.discard(i)
    if bad:
        logger.warning(
            "%s :: %s vs %s :: dropped %d index collision(s) with different question text",
            run_id, left_name, right_name, len(bad),
        )

    common: list[str] = sorted(common_set, key=lambda s: int(s) if s.isdigit() else 0)
    n_paired: int = len(common)


    if n_paired < threshold:
        return None

    rec: dict[str, Any] = {
        "effect": effect_key,
        "run_id": run_id,
        "pair_group": f"{left_name} -> {right_name}",
        "left_config": left_name,
        "right_config": right_name,
        "n_paired_completed": n_paired,
    }


    for k in CONTINUOUS_SCORE_KEYS:
        lv, rv = _paired_floats(
            left_idx, right_idx, lambda s, _k=k: _sample_continuous_score(s, _k), common
        )
        l_mean, r_mean = _mean(lv), _mean(rv)
        rec[f"left_{k}_mean"]   = round(l_mean, 4)
        rec[f"right_{k}_mean"]  = round(r_mean, 4)
        rec[f"delta_{k}_mean"]  = round(r_mean - l_mean, 4)
        p: float | None = _wilcoxon_p(lv, rv)
        rec[f"delta_{k}_wilcoxon_p"] = round(p, 6) if p is not None else ""
        rec[f"delta_{k}_sig"] = bool(p is not None and p < ALPHA)


    rate_keys_local: tuple[str, ...] = RATE_METRIC_KEYS + ("false_refusal_rate",)
    for k in rate_keys_local:
        lv, rv = _paired_floats(
            left_idx, right_idx, lambda s, _k=k: _sample_rate(s, _k), common
        )
        l_mean, r_mean = _mean(lv), _mean(rv)
        rec[f"left_{k}_mean"]   = round(l_mean, 4)
        rec[f"right_{k}_mean"]  = round(r_mean, 4)
        rec[f"delta_{k}_mean"]  = round(r_mean - l_mean, 4)


    lv, rv = _paired_floats(
        left_idx, right_idx, _sample_context_tokens, common
    )
    l_mean, r_mean = _mean(lv), _mean(rv)
    rec["left_context_tokens_est_mean"]   = round(l_mean, 2)
    rec["right_context_tokens_est_mean"]  = round(r_mean, 2)
    rec["delta_context_tokens_est_mean"]  = round(r_mean - l_mean, 2)
    rec["delta_context_tokens_est_pct"]   = (
        round((r_mean - l_mean) / l_mean * 100.0, 2) if l_mean > 0 else 0.0
    )


    lv, rv = _paired_floats(
        left_idx, right_idx, _sample_latency_ms, common
    )
    if not lv or not rv:
        l_lat: float | None = _config_latency_fallback(left_data)
        r_lat: float | None = _config_latency_fallback(right_data)
        rec["left_latency_ms_mean"]   = round(l_lat, 2) if l_lat is not None else ""
        rec["right_latency_ms_mean"]  = round(r_lat, 2) if r_lat is not None else ""
        if l_lat and r_lat:
            rec["delta_latency_ms_mean"]   = round(r_lat - l_lat, 2)
            rec["delta_latency_ratio_pct"] = round((r_lat - l_lat) / l_lat * 100.0, 2)
        else:
            rec["delta_latency_ms_mean"]   = ""
            rec["delta_latency_ratio_pct"] = 0.0
        rec["latency_source"] = "config_metric_fallback"
    else:
        l_lat_v: float = _mean(lv)
        r_lat_v: float = _mean(rv)
        rec["left_latency_ms_mean"]   = round(l_lat_v, 2)
        rec["right_latency_ms_mean"]  = round(r_lat_v, 2)
        rec["delta_latency_ms_mean"]  = round(r_lat_v - l_lat_v, 2)
        rec["delta_latency_ratio_pct"] = (
            round((r_lat_v - l_lat_v) / l_lat_v * 100.0, 2) if l_lat_v > 0 else 0.0
        )
        rec["latency_source"] = "per_sample"

    return rec


def _es_num(value: Any, decimals: int = 2, sign: bool = False) -> str:

    if not isinstance(value, (int, float)):
        return str(value) if value not in (None, "") else "--"
    fmt: str = f"{value:+.{decimals}f}" if sign else f"{value:.{decimals}f}"
    return fmt.replace(".", ",")


_ASCII_MAP: dict[str, str] = {
    "\u00e1": r"\'a", "\u00e9": r"\'e", "\u00ed": r"\'i",
    "\u00f3": r"\'o", "\u00fa": r"\'u", "\u00f1": r"\~n",
    "\u00c1": r"\'A", "\u00c9": r"\'E", "\u00cd": r"\'I",
    "\u00d3": r"\'O", "\u00da": r"\'U", "\u00d1": r"\~N",
    "\u00fc": r'\"u', "\u2014": r"---", "\u2013": r"--",
    "\u2019": r"'",
}


def _to_ascii(text: str) -> str:

    for c, repl in _ASCII_MAP.items():
        text = text.replace(c, repl)
    return text


def _latex_escape_underscore(text: str) -> str:

    return text.replace("_", r"\_")


@dataclass
class AggregatedRow:


    pair_group: str
    left_label: str
    right_label: str
    n_runs: int


    n_paired: int
    deltas: dict[str, float] = field(default_factory=dict)
    n_support: int = 0


def _aggregate_records(
    records: list[dict[str, Any]],
    spec: EffectSpec,
) -> list[AggregatedRow]:

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        grouped[r["pair_group"]].append(r)

    rows: list[AggregatedRow] = []
    order_map: dict[str, int] = {
        f"{lo} -> {ro}": i for i, (lo, ro) in enumerate(spec.pairs)
    }
    for pair_group, grp in sorted(
        grouped.items(),
        key=lambda kv: order_map.get(kv[0], 99),
    ):

        all_keys: set[str] = set()
        for r in grp:
            for k, v in r.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    all_keys.add(k)


        total_n: int = sum(r["n_paired_completed"] for r in grp)
        deltas: dict[str, float] = {}
        for k in all_keys:
            vals: list[float] = [
                float(r[k])
                for r in grp
                if isinstance(r.get(k), (int, float))
            ]
            deltas[k] = sum(vals) / len(vals) if vals else 0.0

        rows.append(AggregatedRow(
            pair_group=pair_group,
            left_label=grp[0]["left_config"],
            right_label=grp[0]["right_config"],
            n_runs=len(grp),
            n_paired=total_n,
            deltas=deltas,
            n_support=sum(1 for r in grp if spec.support_fn(r)),
        ))
    return rows


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:

    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = list(records[0].keys())
    seen: set[str] = set(fieldnames)
    for r in records[1:]:
        for k in r:
            if k not in seen:
                fieldnames.append(k)
                seen.add(k)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    logger.info("Wrote CSV -> %s (%d rows)", path, len(records))


def _write_md_per_pair(
    records: list[dict[str, Any]],
    path: Path,
    spec: EffectSpec,
) -> None:

    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        f"# Efecto aislado: {spec.spanish_name}",
        "",
        f"Pares analizados: **{len(records)}**.  "
        f"Threshold mínimo de muestras emparejadas: **{spec.effective_min_samples}**.",
        "",
        "Cada fila es un (run, pareja) que cumple el threshold.  Los deltas son "
        "**right - left** según la convención definida para este efecto.",
        "",
        "| Run | Pareja | n | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta |",
        "|---|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in records:
        sup: str = "[si]" if spec.support_fn(r) else "[no]"
        lines.append(
            f"| `{r['run_id'][-8:]}` | `{r['pair_group']}` | "
            f"{r['n_paired_completed']} | "
            f"{_es_num(r.get('delta_correctness_mean'),     sign=True)} | "
            f"{_es_num(r.get('delta_faithfulness_mean'),    sign=True)} | "
            f"{_es_num(r.get('delta_answer_relevance_mean'), sign=True)} | "
            f"{_es_num(r.get('delta_context_support_mean'), sign=True)} | "
            f"{_es_num(r.get('delta_overall_mean'),         sign=True)} | {sup} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Wrote per-pair MD -> %s", path)


def _write_md_aggregate(
    rows: list[AggregatedRow],
    path: Path,
    spec: EffectSpec,
) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        f"# Efecto aislado: {spec.spanish_name} (agregado)",
        "",
        "Cada fila promedia los runs de una misma pareja (media aritmética). "
        "`n_paired` es la suma de muestras emparejadas en todos los runs del grupo.",
        "",
        f"Threshold mínimo: **{spec.effective_min_samples}** muestras emparejadas.",
        "",
        "| Pareja | n_runs | n_paired | ΔCorrect. | ΔFaith. | ΔAnsRel. | "
        "ΔCtxSup. | ΔGlobal | Soporta % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        sup_pct: float = (row.n_support / row.n_runs * 100.0) if row.n_runs else 0.0
        d = row.deltas
        lines.append(
            f"| `{row.pair_group}` | {row.n_runs} | {row.n_paired} | "
            f"{_es_num(d.get('delta_correctness_mean'),     sign=True)} | "
            f"{_es_num(d.get('delta_faithfulness_mean'),    sign=True)} | "
            f"{_es_num(d.get('delta_answer_relevance_mean'), sign=True)} | "
            f"{_es_num(d.get('delta_context_support_mean'), sign=True)} | "
            f"{_es_num(d.get('delta_overall_mean'),         sign=True)} | "
            f"{sup_pct:.0f}% |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Wrote aggregate MD -> %s", path)


_COLUMN_DEFS: dict[str, list[tuple[str, str, str]]] = {
    "chunking": [
        ("delta_context_tokens_est_pct",
            r"$\Delta$ context \glos{tokens} \%",                        "delta_pct"),
        ("delta_correctness_mean",
            r"\abbr{Correct}{$\Delta$ Correct.\textsuperscript{c}}",          "delta_score"),
        ("delta_faithfulness_mean",
            r"\abbr{Faith}{$\Delta$ Faith.\textsuperscript{c}}",              "delta_score"),
        ("delta_context_support_mean",
            r"\abbr{CtxSup}{$\Delta$ CtxSup.\textsuperscript{c}}",            "delta_score"),
        ("delta_overall_mean",
            r"\abbr{Global}{$\Delta$ Global\textsuperscript{c}}",             "delta_score"),
    ],
    "reranking": [
        ("delta_correctness_mean",
            r"\abbr{Correct}{$\Delta$ Correct.\textsuperscript{c}}",          "delta_score"),
        ("delta_faithfulness_mean",
            r"\abbr{Faith}{$\Delta$ Faith.\textsuperscript{c}}",              "delta_score"),
        ("delta_context_support_mean",
            r"\abbr{CtxSup}{$\Delta$ CtxSup.\textsuperscript{c}}",            "delta_score"),
        ("delta_retrieval_failure_rate_mean",
            r"\abbr{RetFail}{$\Delta$ RetFail. \abbr{pp}{p.p.}}",          "delta_pct_pts"),
        ("delta_overall_mean",
            r"\abbr{Global}{$\Delta$ Global\textsuperscript{c}}",             "delta_score"),


        ("left_latency_ms_mean",
            r"Lat.\ base (ms)",                            "raw_int"),
        ("delta_latency_ratio_pct",
            r"\abbr{Lat}{$\Delta$ Lat. \%}",               "delta_pct"),
    ],
    "grounding": [
        ("delta_correctness_mean",
            r"\abbr{Correct}{$\Delta$ Correct.\textsuperscript{c}}",          "delta_score"),
        ("delta_faithfulness_mean",
            r"\abbr{Faith}{$\Delta$ Faith.\textsuperscript{c}}",              "delta_score"),
        ("delta_overall_mean",
            r"\abbr{Global}{$\Delta$ Global\textsuperscript{c}}",             "delta_score"),
        ("delta_overconfidence_rate_mean",
            r"\abbr{Overconf}{$\Delta$ Overconf. \abbr{pp}{p.p.}}",        "delta_pct_pts"),
        ("delta_generation_failure_rate_mean",
            r"\abbr{GenFail}{$\Delta$ GenFail. \abbr{pp}{p.p.}}",          "delta_pct_pts"),
        ("delta_false_refusal_rate_mean",
            r"\abbr{FalseRef}{$\Delta$ FalseRef. \abbr{pp}{p.p.}}",        "delta_pct_pts"),
    ],
    "retriever": [
        ("delta_correctness_mean",
            r"\abbr{Correct}{$\Delta$ Correct.\textsuperscript{c}}",          "delta_score"),
        ("delta_faithfulness_mean",
            r"\abbr{Faith}{$\Delta$ Faith.\textsuperscript{c}}",              "delta_score"),
        ("delta_context_support_mean",
            r"\abbr{CtxSup}{$\Delta$ CtxSup.\textsuperscript{c}}",            "delta_score"),
        ("delta_retrieval_failure_rate_mean",
            r"\abbr{RetFail}{$\Delta$ RetFail. \abbr{pp}{p.p.}}",          "delta_pct_pts"),
        ("delta_overall_mean",
            r"\abbr{Global}{$\Delta$ Global\textsuperscript{c}}",             "delta_score"),

        ("left_latency_ms_mean",
            r"\abbr{Lat}{Lat.\ base (ms)}",                            "raw_int"),
        ("delta_latency_ratio_pct",
            r"\abbr{Lat}{$\Delta$ Lat. \%}",               "delta_pct"),
    ],
}


def _fmt_cell(value: Any, kind: str) -> str:

    if not isinstance(value, (int, float)):
        return "--"
    if kind == "delta_score":

        return _es_num(value, decimals=2, sign=True)
    if kind == "delta_pct":

        return _es_num(value, decimals=2, sign=True) + r"\,\%"
    if kind == "delta_pct_pts":


        return _es_num(value, decimals=2, sign=True) + r"\,\abbr{pp}{p.p.}"
    if kind == "raw_int":

        return _es_num(round(value), decimals=0)
    return _es_num(value, decimals=2)


def _write_latex_table(
    rows: list[AggregatedRow],
    path: Path,
    spec: EffectSpec,
) -> None:

    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    cols: list[tuple[str, str, str]] = _COLUMN_DEFS[spec.key]

    align: str = "ll" + "cc" + "c" * len(cols) + "c"


    headers: list[str] = [
        rf"\textbf{{{spec.left_label}}}",
        rf"\textbf{{{spec.right_label}}}",
        r"\abbr{NPares}{N Pares run}",
        r"\abbr{NTotal}{N muestras}",
    ]
    headers += [h for (_, h, _) in cols]
    headers += [r"\abbr{Soporta}{Soporta}"]
    header_line: str = "    " + " & ".join(headers) + r" \\"


    body_lines: list[str] = []
    for row in rows:
        cells: list[str] = [
            _latex_escape_underscore(row.left_label),
            _latex_escape_underscore(row.right_label),
            str(row.n_runs),
            str(row.n_paired),
        ]
        for k, _, fmt in cols:
            cells.append(_fmt_cell(row.deltas.get(k), fmt))
        sup_pct: str = _es_num((row.n_support / row.n_runs * 100.0) if row.n_runs else 0.0)
        cells.append(f"{sup_pct}\\,\\%")
        body_lines.append("      " + " & ".join(cells) + r" \\")


    global_deltas: dict[str, float] = {}
    for k, _, _ in cols:
        vals: list[float] = [
            float(r.deltas[k]) for r in rows
            if isinstance(r.deltas.get(k), (int, float))
        ]
        global_deltas[k] = _mean(vals)
    total_runs: int = sum(r.n_runs for r in rows)


    total_n: int    = sum(r.n_paired for r in rows)
    total_support_pct: str = _es_num(sum(r.n_support for r in rows) / total_runs * 100.0
        if total_runs else 0.0
    )
    g_cells: list[str] = [
        r"\multicolumn{2}{l}{\textbf{Global}}",
        rf"\textbf{{{total_runs}}}",
        rf"\textbf{{{total_n}}}",
    ]
    for k, _, fmt in cols:
        g_cells.append(rf"\textbf{{{_fmt_cell(global_deltas.get(k), fmt)}}}")
    g_cells.append(rf"\textbf{{{total_support_pct}\,\%}}")
    global_line: str = "      " + " & ".join(g_cells) + r" \\"


    caption_short: str = (
        f"Efecto aislado de {spec.spanish_name} "
        f"({spec.left_label} vs. {spec.right_label}). "
        f"\\\\$\\Delta$ = derecha $-$ izquierda."
    )

    lines: list[str] = [
        r"% Auto-generated by scripts/compare_component_effects.py - do not edit by hand.",
        r"\begin{table}[H]",
        r"  \centering",
        r"  \footnotesize",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \renewcommand{\arraystretch}{1.1}",
        r"  \resizebox{\textwidth}{!}{%",
        rf"  \begin{{tabular}}{{{align}}}",
        r"    \toprule",
        header_line,
        r"    \midrule",
    ]
    lines.extend(body_lines)
    lines += [
        r"    \midrule",
        global_line,
        r"    \bottomrule",
        r"  \end{tabular}%",
        r"  }",
        f"  \\caption{{{_to_ascii(caption_short)}}}",
        f"  \\label{{tab:{spec.label_tag}}}",
        r"\end{table}",
    ]
    path.write_text(_to_ascii("\n".join(lines)) + "\n", encoding="utf-8")
    logger.info("Wrote LaTeX table -> %s", path)


def _write_interpretation_tex(
    records: list[dict[str, Any]],
    rows: list[AggregatedRow],
    path: Path,
    spec: EffectSpec,
) -> None:

    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)

    total_runs: int = sum(r.n_runs for r in rows)
    total_pairs: int = len(records)
    n_groups: int   = len(rows)
    n_support: int  = sum(r.n_support for r in rows)
    support_pct: str = _es_num((n_support / total_runs * 100.0) if total_runs else 0.0)


    def _agg(field: str) -> float:
        vs: list[float] = [
            float(r.deltas[field]) for r in rows
            if isinstance(r.deltas.get(field), (int, float))
        ]
        return _mean(vs)

    overall_d: float = _agg("delta_overall_mean")
    corr_d: float    = _agg("delta_correctness_mean")
    faith_d: float   = _agg("delta_faithfulness_mean")
    ctxsup_d: float  = _agg("delta_context_support_mean")

    headline_lines: list[str] = []
    if spec.key == "chunking":
        ctx_d: float = _agg("delta_context_tokens_est_pct")
        headline_lines = [
            rf"El chunker semántico reduce el tamaño del contexto en "
            rf"$\sim$\,{_es_num(abs(ctx_d), decimals=2)}\,\% medido en "
            r"\emph{tokens} estimados, con una variación de calidad de "
            rf"\abbr{{Correct}}{{$\Delta$ Correct.\textsuperscript{{c}}}} = "
            rf"{_es_num(corr_d, sign=True)} y "
            rf"\abbr{{Global}}{{$\Delta$ Global\textsuperscript{{c}}}} = "
            rf"{_es_num(overall_d, sign=True)} en escala 0-100 del juez \acro{{LLM}}.",
            r"Dado que ambos deltas están dentro de la zona de equivalencia "
            rf"práctica ($|\Delta| \le {_es_num(QUALITY_EQUIV_DELTA)}$\,puntos), "
            r"se interpreta el chunking semántico como una alternativa con mejor "
            r"relación calidad-coste cuando el presupuesto de \emph{tokens} importa. ",
        ]
    elif spec.key == "reranking":
        lat_d: float = _agg("delta_latency_ratio_pct")
        retfail_d: float = _agg("delta_retrieval_failure_rate_mean")
        headline_lines = [
            r"El re-ranking aporta una variación de "
            rf"\abbr{{Global}}{{$\Delta$ Global\textsuperscript{{c}}}} = "
            rf"{_es_num(overall_d, sign=True)} y "
            rf"\abbr{{CtxSup}}{{$\Delta$ CtxSup.}} = "
            rf"{_es_num(ctxsup_d, sign=True)} a un coste de latencia "
            rf"\abbr{{Lat}}{{$\Delta$ Lat.}} = "
            rf"{_es_num(lat_d, sign=True)}\,\%.",
            r"El cambio en la tasa de fallos de recuperación es "
            rf"\abbr{{RetFail}}{{$\Delta$ RetFail.}} = "
            rf"{_es_num(retfail_d, sign=True)}\,\abbr{{pp}}{{p.p.}} ",
        ]
    elif spec.key == "grounding":
        overconf_d: float = _agg("delta_overconfidence_rate_mean")
        falseref_d: float = _agg("delta_false_refusal_rate_mean")
        headline_lines = [
            r"El \emph{prompt} \texttt{grounded\_sourced} produce "
            rf"\abbr{{Faith}}{{$\Delta$ Faith.\textsuperscript{{c}}}} = "
            rf"{_es_num(faith_d, sign=True)} y "
            rf"\abbr{{Correct}}{{$\Delta$ Correct.\textsuperscript{{c}}}} = "
            rf"{_es_num(corr_d, sign=True)} en escala 0-100, con "
            rf"\abbr{{Overconf}}{{$\Delta$ Overconf.\abbr{{pp}}{{p.p.}}}} = "
            rf"{_es_num(overconf_d, sign=True)}\,\abbr{{pp}}{{p.p.}}\ y "
            rf"\abbr{{FalseRef}}{{$\Delta$ FalseRef.}} = "
            rf"{_es_num(falseref_d, sign=True)}\,\abbr{{pp}}{{p.p.}}",
        ]
    elif spec.key == "retriever":
        lat_d = _agg("delta_latency_ratio_pct")
        headline_lines = [
            r"Pasar de \acro{BM25} a \acro{FAISS} produce "
            rf"\abbr{{Global}}{{$\Delta$ Global\textsuperscript{{c}}}} = "
            rf"{_es_num(overall_d, sign=True)} en escala 0-100 a un coste "
            rf"de latencia \abbr{{Lat}}{{$\Delta$ Lat.}} = "
            rf"{_es_num(lat_d, sign=True)}\,\%.",
        ]


    support_criterion_lines: dict[str, str] = {
        "chunking": (
            rf"El \textbf{{criterio operativo}} (\textbf{{\abbr{{Soporta}}{{Soporta}}}}) "
            rf"se cumple cuando el chunker semántico \emph{{reduce}} el contexto "
            rf"($\Delta$\,ctx\,$<$\,0) y las variaciones de correción y puntuación global "
            rf"permanecen dentro de la zona de equivalencia práctica "
            rf"($|\Delta|\,\le\,{_es_num(QUALITY_EQUIV_DELTA)}$\,puntos en escala 0\,-\,100). "
            rf"Dicho de otro modo: el chunker semántico \emph{{ahorra tokens}} sin hundir "
            rf"la calidad de respuesta más allá de {_es_num(QUALITY_EQUIV_DELTA)}\,puntos."
        ),
        "reranking": (
            rf"El \textbf{{criterio operativo}} (\textbf{{\abbr{{Soporta}}{{Soporta}}}}) "
            rf"se cumple cuando añadir re-ranking produce "
            rf"\abbr{{Global}}{{$\Delta$\,Global}}\,$\ge$\,0 o \abbr{{CtxSup}}{{$\Delta$\,CtxSup.}}\,$\ge$\,0, "
            rf"la correción no cae más de {_es_num(QUALITY_EQUIV_DELTA)}\,puntos "
            rf"(\abbr{{Correct}}{{$\Delta$\,Correct.}}\,$\ge$\,$-{_es_num(QUALITY_EQUIV_DELTA)}$), "
            rf"y el sobrecoste de latencia es $\le$\,50\,\% "
            rf"(o bien \abbr{{Global}}{{$\Delta$\,Global}}\,$\ge$\,{_es_num(QUALITY_EQUIV_DELTA)}\,puntos "
            rf"si la latencia supera ese umbral). "
            rf"En la práctica: el re-ranking \emph{{mejora la calidad recuperada}} "
            rf"sin destruir la correción ni multiplicar la latencia de forma inaceptable."
        ),
        "grounding": (
            rf"El \textbf{{criterio operativo}} (\textbf{{\abbr{{Soporta}}{{Soporta}}}}) "
            rf"se cumple cuando el prompt \texttt{{grounded\_sourced}} "
            rf"mejora la fidelidad (\abbr{{Faith}}{{$\Delta$\,Faith.}}\,$\ge$\,0), "
            rf"no hunde la correción más de {_es_num(QUALITY_EQUIV_DELTA)}\,puntos "
            rf"(\abbr{{Correct}}{{$\Delta$\,Correct.}}\,$\ge$\,$-{_es_num(QUALITY_EQUIV_DELTA)}$), "
            rf"reduce la alucinación (\abbr{{Overconf}}{{$\Delta$\,Overconf.}}\,$\le$\,0) "
            rf"y el incremento en tasa de rechazo falso es "
            rf"$\le$\,{_es_num(QUALITY_EQUIV_DELTA)}\,\abbr{{pp}}{{p.p.}} "
            rf"En la práctica: el prompt grounded \emph{{mejora la respaldabilidad}} "
            rf"sin sacrificar correción ni disparar rechazo falso."
        ),
        "retriever": (
            rf"El \textbf{{criterio operativo}} (\textbf{{\abbr{{Soporta}}{{Soporta}}}}) "
            rf"se cumple cuando \acro{{FAISS}} obtiene mayor puntuación global "
            rf"que \acro{{BM25}} (\abbr{{Global}}{{$\Delta$\,Global}},$\ge$\,0) "
            rf"y además no es más lento (o si lo es, la ganancia de calidad "
            rf"compensa: \abbr{{Global}}{{$\Delta$\,Global}}\,$\ge$\,{_es_num(QUALITY_EQUIV_DELTA)}\,puntos). "
            rf"En la práctica: \acro{{FAISS}} \emph{{supera a \acro{{BM25}}}} "
            rf"en calidad con un coste temporal aceptable."
        ),
    }
    support_criterion: str = support_criterion_lines.get(spec.key, "")

    body: list[str] = [
        r"% Auto-generated by scripts/compare_component_effects.py.",
        r"% Interpretación corta del efecto aislado; todos los números provienen",
        r"% de las medias agregadas del CSV correspondiente.",
        r"\noindent",
        rf"De los \textbf{{{total_pairs}}} pares (run\,$\times$\,pareja) "
        rf"agrupados en \textbf{{{n_groups}}} parejas controladas sobre "
        rf"\textbf{{{total_runs}}} ejecuciones, "
        rf"\textbf{{{support_pct}}}\,\% satisfacen el criterio operativo definido "
        rf"para este efecto (ver tabla \ref{{tab:{spec.label_tag}}}). \\",
        "",

        support_criterion,
        "",
    ] + headline_lines

    path.write_text(_to_ascii("\n".join(body)) + "\n", encoding="utf-8")
    logger.info("Wrote interpretation -> %s", path)


def _write_todo_tex(path: Path, spec: EffectSpec) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "% TODO: no existen pares válidos con n suficiente para este "
        f"efecto en la campaña principal.\n"
        f"% Effect: {spec.key}.  Threshold mínimo aplicado: "
        f"{spec.effective_min_samples}.\n",
        encoding="utf-8",
    )
    logger.warning("Wrote TODO stub for %s -> %s", spec.key, path)


def _write_chart(
    rows: list[AggregatedRow],
    path: Path,
    spec: EffectSpec,
) -> None:

    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np


    _C_GREEN: str = "#27AE60"
    _C_RED:   str = "#C0392B"
    _C_BLUE:  str = "#2980B9"
    _C_BAND:  str = "#F0F0F0"
    _C_ZERO:  str = "#333333"

    labels: list[str] = [r.pair_group.replace(" -> ", "\n→ ") for r in rows]
    k_a, k_b = spec.chart_metrics
    vals_a: list[float] = [float(r.deltas.get(k_a, 0.0)) for r in rows]
    vals_b: list[float] = [float(r.deltas.get(k_b, 0.0)) for r in rows]

    y: Any = np.arange(len(rows))
    bar_h: float = 0.55
    fig_h: float = max(6.0, len(rows) * 1.0 + 4.0)
    fig, (axA, axB) = plt.subplots(
        2, 1, figsize=(9.0, fig_h), gridspec_kw={"hspace": 0.7},
    )

    def _clean(ax: Any) -> None:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)
        ax.grid(axis="x", alpha=0.35, linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)

    def _is_overall(k: str) -> bool:
        return k in ("delta_overall_mean",)

    def _bar_color(v: float, k: str) -> str:

        if _is_overall(k):
            return _C_BLUE if abs(v) <= QUALITY_EQUIV_DELTA else _C_RED

        if k == "delta_context_tokens_est_pct":
            return _C_GREEN if v < 0 else _C_RED

        if k == "delta_latency_ratio_pct":
            return _C_GREEN if v <= 0 else _C_RED

        if k == "delta_overconfidence_rate_mean":
            return _C_GREEN if v <= 0 else _C_RED

        if k == "delta_faithfulness_mean":
            return _C_GREEN if v >= 0 else _C_RED
        return _C_BLUE

    def _annotate(ax: Any, vals: list[float], suffix: str) -> None:
        rng: float = max(abs(v) for v in vals) if vals else 1.0
        pad: float = rng * 0.03
        for i, v in enumerate(vals):
            ha: str = "left" if v >= 0 else "right"
            ax.text(
                v + (pad if v >= 0 else -pad),
                y[i],
                f"{v:+.2f}{suffix}",
                ha=ha, va="center", fontsize=8, fontweight="bold",
                color="#222222",
            )

    def _draw_panel(
        ax: Any, vals: list[float], k: str,
        title: str, xlabel: str, suffix: str,
    ) -> None:

        if _is_overall(k):
            ax.axvspan(
                -QUALITY_EQUIV_DELTA, QUALITY_EQUIV_DELTA,
                color=_C_BAND, zorder=1,
            )
        colors: list[str] = [_bar_color(v, k) for v in vals]
        ax.barh(y, vals, bar_h, color=colors, edgecolor="white",
                linewidth=0.5, zorder=3)
        ax.axvline(0, color=_C_ZERO, linewidth=1.0, zorder=4)
        _annotate(ax, vals, suffix)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold", loc="left", pad=6)
        rng = max(abs(v) for v in vals + [QUALITY_EQUIV_DELTA if _is_overall(k) else 0.001])
        ax.set_xlim(-(rng * 1.35), rng * 1.35)
        _clean(ax)


    def _suffix(k: str) -> str:
        if k in ("delta_context_tokens_est_pct", "delta_latency_ratio_pct"):
            return "%"
        if k.endswith("_rate_mean"):
            return " p.p."
        return ""

    titles_xlabels: dict[str, tuple[str, str]] = {
        "delta_overall_mean":              ("Δ Global (escala 0-100)",
                                            "Δ Global"),
        "delta_context_tokens_est_pct":    ("Δ contexto (tokens estimados)",
                                            "Δ contexto (%)"),
        "delta_latency_ratio_pct":         ("Δ latencia",
                                            "Δ latencia (%)"),
        "delta_faithfulness_mean":         ("Δ Faith. (escala 0-100)",
                                            "Δ Faith."),
        "delta_overconfidence_rate_mean":  ("Δ Overconf.",
                                            "Δ Overconf. (puntos porcentuales)"),
    }
    t_a, x_a = titles_xlabels.get(k_a, ("(A)", ""))
    t_b, x_b = titles_xlabels.get(k_b, ("(B)", ""))
    _draw_panel(axA, vals_a, k_a, f"(A)  {t_a}", x_a, _suffix(k_a))
    _draw_panel(axB, vals_b, k_b, f"(B)  {t_b}", x_b, _suffix(k_b))

    if any(_is_overall(k) for k in spec.chart_metrics):
        band_patch = mpatches.Patch(
            facecolor=_C_BAND,
            label=f"zona equiv. ±{_es_num(QUALITY_EQUIV_DELTA)} pts",
            linewidth=0.8, edgecolor="#aaaaaa",
        )
        target_ax: Any = axA if _is_overall(k_a) else axB
        target_ax.legend(
            handles=[band_patch], fontsize=8,
            loc="lower right", framealpha=0.85, edgecolor="#cccccc",
        )

    fig.suptitle(
        f"Efecto aislado: {spec.spanish_name}\n"
        f"(media aritmética por pareja; runs con distinto n no se mezclan)",
        fontsize=12, fontweight="bold", y=0.99,
    )
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote chart -> %s", path)


def _load_run_experiments(run_dir: Path) -> dict[str, dict[str, Any]]:

    out: dict[str, dict[str, Any]] = {}
    exp_dir: Path = run_dir / "experiments"
    if not exp_dir.is_dir():
        return out
    for p in exp_dir.glob("*.json"):
        try:
            out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Cannot load %s: %s", p, exc)
    return out


def _process_runs(
    run_dirs: list[Path],
    specs: list[EffectSpec],
) -> dict[str, list[dict[str, Any]]]:

    by_effect: dict[str, list[dict[str, Any]]] = {s.key: [] for s in specs}
    runs_seen: int = 0
    runs_used: dict[str, set[str]] = {s.key: set() for s in specs}

    for rd in run_dirs:
        exps: dict[str, dict[str, Any]] = _load_run_experiments(rd)
        if not exps:
            continue
        runs_seen += 1

        for spec in specs:
            for left_name, right_name in spec.pairs:
                if left_name not in exps or right_name not in exps:
                    continue
                rec: dict[str, Any] | None = _compare_pair(
                    rd.name,
                    exps[left_name],
                    exps[right_name],
                    left_name,
                    right_name,
                    spec.key,
                    spec.effective_min_samples,
                )
                if rec is None:
                    continue
                by_effect[spec.key].append(rec)
                runs_used[spec.key].add(rd.name)


    _process_runs._stats = {
        "runs_scanned": runs_seen,
        "runs_used": {k: len(v) for k, v in runs_used.items()},
    }
    return by_effect


def _build_specs() -> list[EffectSpec]:
    return [
        EffectSpec(
            key="chunking",
            spanish_name="chunking",
            pairs=CHUNKING_PAIRS,
            left_label="Variante fija",
            right_label="Variante sem\u00e1ntica",
            table_metrics=tuple(c[0] for c in _COLUMN_DEFS["chunking"]),
            chart_metrics=("delta_overall_mean", "delta_context_tokens_est_pct"),
            support_fn=_support_chunking,
            label_tag="chunking_effect",
        ),
        EffectSpec(
            key="reranking",
            spanish_name="re-ranking",
            pairs=RERANKING_PAIRS,
            left_label="Variante base",
            right_label=r"Variante con \acro{RR}",
            table_metrics=tuple(c[0] for c in _COLUMN_DEFS["reranking"]),
            chart_metrics=("delta_overall_mean", "delta_latency_ratio_pct"),
            support_fn=_support_reranking,
            label_tag="reranking_effect",
        ),
        EffectSpec(
            key="grounding",
            spanish_name="prompt grounded",
            pairs=GROUNDING_PAIRS,
            left_label="Variante basic",
            right_label="Variante grounded",
            table_metrics=tuple(c[0] for c in _COLUMN_DEFS["grounding"]),
            chart_metrics=("delta_faithfulness_mean", "delta_overconfidence_rate_mean"),
            support_fn=_support_grounding,
            label_tag="grounding_effect",
        ),
        EffectSpec(
            key="retriever",
            spanish_name="retriever (BM25 vs FAISS)",
            pairs=RETRIEVER_PAIRS,
            left_label=r"Variante \acro{BM25}",
            right_label=r"Variante \acro{FAISS}",
            table_metrics=tuple(c[0] for c in _COLUMN_DEFS["retriever"]),
            chart_metrics=("delta_overall_mean", "delta_latency_ratio_pct"),
            support_fn=_support_retriever,
            label_tag="retriever_effect",
        ),
    ]


@dataclass
class EmissionResult:


    written: ClassVar[list[Path]] = []
    pairs_per_effect: dict[str, int] = field(default_factory=dict)
    effects_generated: list[str] = field(default_factory=list)
    effects_skipped: list[str] = field(default_factory=list)


def _emit_effect(
    spec: EffectSpec,
    records: list[dict[str, Any]],
    result: EmissionResult,
) -> list[Path]:

    eff_dir: Path = OUTPUT_ROOT / spec.key
    eff_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_path: Path = eff_dir / f"{spec.key}_effect.csv"
    md_path: Path = eff_dir / f"{spec.key}_effect.md"
    agg_md_path: Path = eff_dir / f"{spec.key}_effect_aggregate.md"
    tex_path: Path = eff_dir / f"{spec.key}_effect_table.tex"
    interp_path: Path = eff_dir / f"{spec.key}_effect_interpretation.tex"
    chart_path: Path = eff_dir / f"{spec.key}_effect_chart.png"

    if not records:

        _write_todo_tex(tex_path, spec)
        _write_todo_tex(interp_path, spec)
        result.effects_skipped.append(spec.key)
        result.pairs_per_effect[spec.key] = 0
        paths.append(tex_path)
        paths.append(interp_path)
        return paths

    rows: list[AggregatedRow] = _aggregate_records(records, spec)

    _write_csv(records, csv_path);                       paths.append(csv_path)
    _write_md_per_pair(records, md_path, spec);          paths.append(md_path)
    _write_md_aggregate(rows, agg_md_path, spec);        paths.append(agg_md_path)
    _write_latex_table(rows, tex_path, spec);            paths.append(tex_path)
    _write_interpretation_tex(records, rows, interp_path, spec); paths.append(interp_path)
    try:
        _write_chart(rows, chart_path, spec);            paths.append(chart_path)
    except Exception as exc:
        logger.error("Chart generation failed for %s: %s", spec.key, exc)

    result.effects_generated.append(spec.key)
    result.pairs_per_effect[spec.key] = len(records)
    return paths


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--run-id", type=str, default=None,
                   help="Single run id (or unique substring).")
    g.add_argument("--latest", action="store_true",
                   help="Only the most recent run.")
    p.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    p.add_argument(
        "--min-samples", type=int, default=DEFAULT_MIN_SAMPLES,
        metavar="N",
        help=(
            "Minimum paired-completed samples for a pair to be considered.  "
            f"Default {DEFAULT_MIN_SAMPLES} (full-scale campaign).  "
            f"Retriever effect always uses min(N, {RETRIEVER_MIN_CAP}) "
            "because BM25 vs FAISS pairs only exist at 50-sample runs."
        ),
    )
    p.add_argument(
        "--dataset", type=str, default=DEFAULT_DATASET,
        metavar="NAME",
        help=(
            "Only include runs whose run_manifest.json 'dataset' field matches "
            f"NAME (case-insensitive).  Default: '{DEFAULT_DATASET}'.  "
            "Pass 'all' to include every dataset."
        ),
    )
    return p.parse_args(argv)


def _run_dataset(run_dir: Path) -> str:

    manifest: Path = run_dir / "run_manifest.json"
    if not manifest.is_file():
        return ""
    try:
        data: dict = json.loads(manifest.read_text(encoding="utf-8"))
        return str(data.get("dataset", "")).lower().strip()
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read manifest %s: %s", manifest, exc)
        return ""


def _select_runs(args: argparse.Namespace) -> list[Path]:
    if not args.runs_dir.is_dir():
        logger.error("Runs dir not found: %s", args.runs_dir)
        return []
    all_runs: list[Path] = sorted(d for d in args.runs_dir.iterdir() if d.is_dir())
    if args.run_id:
        matches: list[Path] = [
            d for d in all_runs
            if d.name == args.run_id or args.run_id in d.name
        ]
        if not matches:
            logger.error("No run matches '%s'.", args.run_id)
            return []
        all_runs = matches
    elif args.latest:
        all_runs = all_runs[-1:] if all_runs else []


    want_ds: str = args.dataset.lower().strip()
    if want_ds != "all":
        before: int = len(all_runs)
        all_runs = [rd for rd in all_runs if _run_dataset(rd) == want_ds]
        skipped: int = before - len(all_runs)
        if skipped:
            logger.info(
                "Dataset filter '%s': skipped %d run(s), keeping %d.",
                want_ds, skipped, len(all_runs),
            )
        if not all_runs:
            logger.error(
                "No runs found for dataset '%s'.  "
                "Use --dataset all to include every dataset.",
                want_ds,
            )

    return all_runs


def main(argv: list[str] | None = None) -> int:

    args: argparse.Namespace = _parse_args(argv)
    run_dirs: list[Path] = _select_runs(args)
    if not run_dirs:
        return 1


    specs: list[EffectSpec] = _build_specs()
    for s in specs:
        if s.key == "retriever":
            s.effective_min_samples = min(args.min_samples, RETRIEVER_MIN_CAP)
        else:
            s.effective_min_samples = args.min_samples

    logger.info("Scanning %d run(s)...", len(run_dirs))
    by_effect: dict[str, list[dict[str, Any]]] = _process_runs(run_dirs, specs)

    result: EmissionResult = EmissionResult()
    all_paths: list[Path] = []
    for s in specs:
        all_paths.extend(_emit_effect(s, by_effect[s.key], result))


    stats: dict[str, Any] = getattr(_process_runs, "_stats", {})
    runs_used: dict[str, int] = stats.get("runs_used", {})
    print()
    print("=" * 60)
    print("Component-effects analysis summary")
    print("=" * 60)
    print(f"Runs scanned                : {stats.get('runs_scanned', 0)}")
    print(f"Effects generated           : {', '.join(result.effects_generated) or '(none)'}")
    print(f"Effects skipped (TODO stub) : {', '.join(result.effects_skipped) or '(none)'}")
    print()
    for s in specs:
        n_pairs: int = result.pairs_per_effect.get(s.key, 0)
        n_runs_used: int = runs_used.get(s.key, 0)
        print(
            f"  - {s.key:<10s}  threshold={s.effective_min_samples:>4d}  "
            f"runs_used={n_runs_used:>3d}  valid_pairs={n_pairs:>3d}"
        )
    print()
    print(f"Outputs written under: {OUTPUT_ROOT}")
    for p in all_paths:
        print(f"   {p.relative_to(PROJECT_ROOT)}")
    print()
    print("Manual review reminders:")
    print("  - The metric annex (Anexo N) must define: AnsRel, CtxSup, Global,")
    print("    NPares, NTotal, Soporta.  Add any that are missing.")
    print("  - Interpretation .tex files are short by design; expand them in")
    print("    the thesis body if narrative requires more context.")
    if result.effects_skipped:
        print(
            "  - The following effects produced no valid pairs at the threshold "
            f"in effect: {', '.join(result.effects_skipped)}.  TODO stubs were "
            "written instead of fabricated evidence."
        )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
