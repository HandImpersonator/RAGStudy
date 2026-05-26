# Estructura del directorio `output/` y logs

El directorio `output/thesis/` contiene los artefactos generados para la memoria.
El directorio `logs/` contiene todos los datos de experimentos.

---

## Árbol real de `output/thesis/` (artefactos de tesis)

```
output/thesis/
├── thesis.tex                          ← memoria compilada (generada por thesis_generator.py)
├── logo.png
├── budget/
│   ├── budget_macros.tex
│   └── budget_table.tex
│
├── main_experiments/
│   ├── chunking/
│   │   ├── chunking_efficiency_chart.png
│   │   ├── chunking_efficiency_table.tex
│   │   └── chunking_efficiency_interpretation.tex
│   ├── component_effects/
│   │   ├── chunking/
│   │   │   ├── chunking_effect_chart.png
│   │   │   ├── chunking_effect_table.tex
│   │   │   └── chunking_effect_interpretation.tex
│   │   ├── reranking/
│   │   │   ├── reranking_effect_chart.png
│   │   │   ├── reranking_effect_table.tex
│   │   │   └── reranking_effect_interpretation.tex
│   │   ├── grounding/
│   │   │   ├── grounding_effect_chart.png
│   │   │   ├── grounding_effect_table.tex
│   │   │   └── grounding_effect_interpretation.tex
│   │   └── retriever/
│   │       ├── retriever_effect_chart.png
│   │       ├── retriever_effect_table.tex
│   │       └── retriever_effect_interpretation.tex
│   ├── cross_model/triviaqa/thesis_compact/
│   │   ├── cross_model_table.tex
│   │   ├── cross_model_correctness_mean.png      + *_table.tex
│   │   ├── cross_model_faithfulness_mean.png      + *_table.tex
│   │   ├── cross_model_answer_relevance_mean.png  + *_table.tex
│   │   ├── cross_model_answer_accuracy.png        + *_table.tex
│   │   ├── cross_model_context_sufficiency_rate.png + *_table.tex
│   │   ├── cross_model_contradiction_rate.png     + *_table.tex
│   │   ├── cross_model_faithfulness_rate.png      + *_table.tex
│   │   ├── cross_model_overconfidence_rate.png    + *_table.tex
│   │   ├── cross_model_failure_breakdown.png
│   │   └── cross_model_rate_metrics.png
│   └── triviaqa/
│       ├── llama3-8b/
│       │   ├── thesis_compact/
│       │   │   ├── quality_comparison.png
│       │   │   ├── failure_type_breakdown.png
│       │   │   ├── final_results_table.tex
│       │   │   └── final_results_interpretation.tex
│       │   ├── diagnostics/
│       │   │   ├── latency_breakdown.png
│       │   │   ├── rate_metrics_comparison.png
│       │   │   ├── radar_chart.png
│       │   │   └── overconfidence_chart.png
│       │   └── appendix/
│       │       └── comparison_table.tex
│       └── mistral-7b/
│           └── (misma estructura que llama3-8b/)
│
└── model_selection/
    ├── cross_model/triviaqa/thesis_compact/
    │   ├── cross_model_table.tex
    │   ├── cross_model_*.png  + *_table.tex     (mismas figuras que main_experiments)
    │   ├── model_selection_decision.tex
    │   ├── model_selection_interpretation.tex
    │   ├── config_screening_cross_model_decision.tex
    │   ├── config_screening_cross_model_interpretation.tex
    │   ├── bm25_quality_cost_cross_model_evidence.tex
    │   └── bm25_quality_cost_cross_model_interpretation.tex
    └── triviaqa/
        ├── llama3.2-latest/
        │   ├── thesis_compact/
        │   │   ├── quality_comparison.png
        │   │   ├── failure_type_breakdown.png
        │   │   ├── config_screening_decision.tex
        │   │   ├── config_screening_interpretation.tex
        │   │   ├── bm25_interpretation.tex
        │   │   └── bm25_quality_cost_evidence.tex
        │   ├── diagnostics/
        │   │   ├── latency_breakdown.png
        │   │   ├── rate_metrics_comparison.png
        │   │   ├── radar_chart.png
        │   │   └── overconfidence_chart.png
        │   └── appendix/
        │       └── comparison_table.tex
        ├── llama3-8b/   (misma estructura que llama3.2-latest/)
        └── mistral-7b/  (misma estructura que llama3.2-latest/)
```

---

## Árbol de `output/comparison/` (artefactos del barrido retriever×reranker)

```
output/comparison/combo_sweep/<dataset>/<llm_scope>/
    thesis_compact/         ← tablas LaTeX compactas para la memoria
    appendix/               ← evidencias detalladas
    raw_evidence/           ← JSON de métricas por combo
    diagnostics_per_combo/  ← (solo con --with-diagnostics)
```

---

## Estructura de `logs/`

```
logs/
├── cli_runs/                            ← logs de consola de cada invocación de script
│   └── run_YYYYMMDD_HHMMSS.log          (N=~80 archivos)
│
├── index/
│   └── run_index.jsonl                  ← índice JSONL de todas las ejecuciones
│
├── summaries/                           ← resúmenes schema 2.0 (108 archivos)
│   ├── <run_id>__experiment_summary.json
│   └── <run_id>__experiment_summary_human.md
│
└── runs/                                ← 52 ejecuciones totales
    └── <run_id>/                        ← ej: run_20260518_204035_unknown_e7e4e2d8/
        ├── run_manifest.json
        ├── artifact_metadata.json        (solo en runs marcados con familia)
        ├── experiments/
        │   ├── no_rag.json
        │   ├── baseline_k.json
        │   ├── baseline_s.json
        │   ├── baseline_k_rr.json
        │   ├── …                         (× 17 configs máximo)
        │   └── optimized_s_rr_grounded.json
        ├── summaries/
        │   ├── experiment_summary.json
        │   └── experiment_summary_human.md
        └── evaluation_artifacts/         (solo si hubo Batch API fallback)
            └── <config>/
```

### Estructura interna de un `experiments/<config>.json`

```json
{
  "schema_version": "2.0",
  "run_id": "run_20260518_204035_unknown_e7e4e2d8",
  "config_name": "baseline_k_rr",
  "dataset": "triviaqa",
  "model_label": "llama3-8b",
  "samples": [
    {
      "index": 0,
      "eval_item_id": "run_...::baseline_k_rr::0000",
      "question": "...",
      "ground_truth": "...",
      "answer": "...",
      "sources": [ { "chunk_global_id": "...", "doc_id": "...", ... } ],
      "timings_ms": { "retrieval_ms": 12.4, "reranking_ms": 8.1, ... },
      "eval": {
        "status": "completed",
        "scores": { "correctness": 85.0, "faithfulness": 90.0, ... },
        "judge_notes": {
          "answer_correct": true,
          "context_sufficient": true,
          "is_refusal": false,
          "failure_type": "none",
          ...
        }
      }
    }
  ],
  "stats": {
    "correctness_mean": 72.4,
    "overconfidence_rate": 3.2,
    "generation_fail_rate": 11.4,
    "latency_mean_ms": 1243.5,
    ...
  }
}
```

### Estructura de `experiment_summary.json`

```json
{
  "schema_version": "2.0",
  "run_id": "...",
  "dataset": "triviaqa",
  "model_label": "llama3-8b",
  "configs": {
    "baseline_k_rr": {
      "metrics": [
        { "tag": "THESIS_METRIC", "metric": "correctness_mean", "value": 72.4,
          "n_evaluated": 500, "config": "baseline_k_rr", ... },
        { "tag": "THESIS_METRIC", "metric": "overconfidence_rate", "value": 3.2, ... },
        ...
      ]
    }
  }
}
```

---

## Numeración de figuras, tablas y ficheros de datos en la memoria

### Figuras PNG usadas en la memoria (`\includegraphics`)

**Selección de modelo (model_selection/triviaqa/)**

| Archivo | Contenido |
|---------|-----------|
| `<model>/thesis_compact/quality_comparison.png` | Barras de métricas de calidad por config |
| `<model>/thesis_compact/failure_type_breakdown.png` | Desglose tipos de fallo |
| `<model>/diagnostics/latency_breakdown.png` | Latencia desglosada por fase |
| `<model>/diagnostics/rate_metrics_comparison.png` | Tasas de fallo comparadas |
| `<model>/diagnostics/radar_chart.png` | Radar multimétrico |
| `<model>/diagnostics/overconfidence_chart.png` | Alucinación por config |

**Cross-model (cross_model/triviaqa/thesis_compact/)**

| Archivo | Contenido |
|---------|-----------|
| `cross_model_correctness_mean.png` | Correctness por config × modelo |
| `cross_model_faithfulness_mean.png` | Faithfulness por config × modelo |
| `cross_model_answer_relevance_mean.png` | Relevance por config × modelo |
| `cross_model_failure_breakdown.png` | Tipos de fallo × modelo |
| `cross_model_rate_metrics.png` | Tasas de fallo × modelo |
| `cross_model_overconfidence_rate.png` | Alucinación × modelo |

**Efectos de componentes (main_experiments/component_effects/)**

| Archivo | Efecto medido |
|---------|---------------|
| `chunking/chunking_effect_chart.png` | SemanticChunker vs FixedChunker |
| `reranking/reranking_effect_chart.png` | CrossEncoder vs NoReranker |
| `grounding/grounding_effect_chart.png` | grounded_sourced vs basic prompt |
| `retriever/retriever_effect_chart.png` | FAISS vs BM25 |

### Tablas LaTeX usadas en la memoria (`\input`)

| Archivo | Contenido |
|---------|-----------|
| `cross_model_table.tex` | Tabla resumen cross-modelo (Correct., Faith., Global, Relev., Alucinación, GenFail., Lat.) |
| `comparison_table.tex` | Tabla detallada de todas las métricas por config |
| `final_results_table.tex` | Tabla de resultados finales con IC bootstrap |
| `*_effect_table.tex` | Efecto aislado de cada componente con p-valor y Cohen d |
| `config_screening_decision.tex` | Decisión y justificación de configs eliminadas |
| `model_selection_decision.tex` | Decisión de selección de modelo |
| `budget_table.tex` | Desglose del presupuesto del proyecto |

### Datos brutos consultables

| Path | Descripción |
|------|-------------|
| `logs/index/run_index.jsonl` | Índice JSONL de las 52 ejecuciones |
| `logs/summaries/<run_id>__experiment_summary.json` | 54 resúmenes schema 2.0 |
| `logs/runs/<run_id>/experiments/<config>.json` | JSONs de experimentos (17 configs × 52 runs) |
| `logs/runs/<run_id>/run_manifest.json` | Manifiesto de la ejecución |
| `logs/cli_runs/run_YYYYMMDD_HHMMSS.log` | ~80 logs de consola |
| `.cache/rag/<stage>/<key16>/manifest.json` | Manifests de cache por etapa |

