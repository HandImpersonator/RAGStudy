# Módulo de experimentos y flujo operativo

## Propósito

Ejecutar ejecuciones comparables entre las 17 configuraciones y dejar artefactos
reproducibles para análisis posterior. El runner gestiona el ciclo completo:
ejecución → evaluación Phase 2 → resumen → índice.

> Para la división exacta de responsabilidades entre
> `run_retriever_comparison.py`, `run_experiments.py` y `generate_charts.py`

## Runner principal

1. Archivo `scripts/run_experiments.py`.
2. Ejecutable directamente: `python3 scripts/run_experiments.py`.
3. Admite `--dry-run` para validar configuración sin ejecutar el LLM.
4. `EXPERIMENT_ORDER: list[tuple[int, str]]` - orden de ejecución (1-17).
5. `DISABLED_CONFIGS: frozenset[str]` - excluye configs sin borrarlas;
   comentar/descomentar por experimento.

## Preflight automático

Antes de lanzar, el runner verifica:
1. Conectividad con servidor remoto (Ollama).
2. Modelo activo en el servidor.
3. Existencia de corpus e índices requeridos por las configs activas.
4. Disponibilidad de `OPENAI_API_KEY` (opcional - Phase 2).
5. Ajusta parámetros (`top_k`, `batch_size`) según modelo detectado.

## Flujo completo (schema 2.0)

1. `create_run_id()` - identificador único de la ejecución.
2. Prewarm de cache (si `--prewarm-cache`, activo por defecto).
3. Ejecutar configuraciones activas en `EXPERIMENT_ORDER`.
4. Guardar `experiments/<config>.json` con schema 2.0 tras cada config.
5. Actualizar `run_manifest.json` tras cada config.
6. **Phase 2 - evaluación con juez LLM OpenAI** (si `OPENAI_API_KEY`):
   a. Lotes síncronos por config (Responses API + Structured Outputs).
   b. Reescritura de `samples[].eval` en los mismos JSON.
   c. Recomputar métricas de calidad (`recompute_llm_eval_metrics`).
   d. Si hay pendientes y `OPENAI_EVAL_ASYNC_BATCH_FALLBACK=true`: Batch API.
7. `regenerate_summary_for_run()` - resumen v2.0 con métricas actualizadas.
8. Copia del resumen a `logs/summaries/<run_id>__experiment_summary.json`.
9. `append_to_run_index()` - entrada en `logs/index/run_index.jsonl`.

## Estructura de salida

```
logs/runs/<run_id>/
    run_manifest.json
    experiments/<config_name>.json   (× 17)
    summaries/
        experiment_summary.json
        experiment_summary_human.md
logs/summaries/<run_id>__experiment_summary.json
logs/index/run_index.jsonl
```

## Esquema de datos (schema 2.0)

- `schema_version` = `"2.0"`.
- `run_id` común en toda la ejecución.
- `eval_item_id` por muestra: `"{run_id}::{config_name}::{index:04d}"`.
- `sources: list[SourceInfo]` con trazabilidad completa de cada chunk.
- Bloque `eval` con métricas del juez LLM (o `pending` si Phase 2 no corrió).
- Métricas de rendimiento agregadas en `stats`.

## Métricas registradas

### Latencia y rendimiento (siempre disponibles)

1. `latency_mean_ms`
2. `retrieval_time_mean_ms`
3. `generation_time_mean_ms`
4. `answer_length_tokens_mean`
5. `memory_peak_mb`
6. `num_samples`

### Calidad (Phase 2, requiere juez LLM)

1. `correctness_mean` (0-100)
2. `faithfulness_mean` (0-100)
3. `answer_relevance_mean` (0-100)
4. `context_support_mean` (0-100)
5. `refusal_quality_mean` (0-100)
6. `overall_mean` (0-100)
7. `refusal_rate` - fracción de respuestas que fueron negativas.
8. `false_refusal_rate` - fracción de negativas injustificadas.

### Métricas de failure attribution (calculadas de `judge_notes`)

| Métrica                  | Descripción                                                    |
|--------------------------|----------------------------------------------------------------|
| `retrieval_fail_rate`    | % de muestras con `failure_type == "retrieval_failure"`        |
| `generation_fail_rate`   | % de muestras con `failure_type == "generation_failure"`       |
| `combined_failure_rate`  | % de muestras con `failure_type == "both"`                     |
| `overconfidence_rate`    | % de respuestas incorrectas sin contexto pero con alta relevancia (`answer_relevance >= 70`) |
| `answer_accuracy`        | % de muestras con `answer_correct == true`                     |
| `context_sufficiency_rate` | % de muestras con `context_sufficient == true`               |
| `faithfulness_rate`      | % de muestras con `answer_supported_by_context == true`        |

## Parámetros CLI

| Flag                   | Descripción                                         |
|------------------------|-----------------------------------------------------|
| `--configs`            | Lista de números de config (1-17) a ejecutar.       |
| `--dataset`            | Dataset a usar (e.g. `hotpotqa`, `triviaqa`).       |
| `--max-samples`        | Número máximo de muestras por config.               |
| `--dry-run`            | Valida sin ejecutar el LLM.                         |
| `--no-eval`            | Omite Phase 2 aunque haya API key.                  |
| `--prewarm-cache` / `--no-prewarm-cache` | Control del prewarm automático. |
| `--use-cache` / `--no-use-cache` | Activar/desactivar cache.             |
| `--cached-only`        | Abortar si hay cualquier CACHE_MISS.                |
| `--model-label`        | Etiqueta del modelo para logs.                      |

## Flujo operativo recomendado

```bash
# 1. Verificar entorno
python3 scripts/verify_setup.py

# 2. Probar conectividad end-to-end
python3 scripts/quick_test.py

# 3. (Opcional) Pre-computar artefactos de cache
python3 scripts/prepare_rag_artifacts.py --dataset triviaqa \
    --chunkers fixed semantic --retrievers bm25 faiss \
    --retrieval-models sentence-transformers/multi-qa-MiniLM-L6-cos-v1 \
    --rerankers cross-encoder/ms-marco-MiniLM-L-6-v2 \
    --top-k 25 --reranker-top-n 5 --max-samples 500

# 4. Dry-run para validar configuración
python3 scripts/run_experiments.py --dry-run --dataset triviaqa

# 5. Ejecución completa (prewarm automático si no se hizo el paso 3)
python3 scripts/run_experiments.py --dataset triviaqa

# 6. Marcar como familia model_selection (opcional, si es Paso 2)
echo '{"experiment_family": "model_selection"}' \
    > logs/runs/<run_id>/artifact_metadata.json

# 7. Generar gráficas
python3 scripts/generate_charts.py
python3 scripts/generate_charts.py --include-family model_selection
```

## Flags de cache en los runners

| Flag | Default | Descripción |
|------|---------|-------------|
| `--use-cache` / `--no-use-cache` | `True` | Activar/desactivar cache |
| `--cached-contexts` / `--no-cached-contexts` | `True` | Cargar contexts precalculados |
| `--prewarm-cache` / `--no-prewarm-cache` | `True` | Prewarm automático antes del bucle |
| `--cached-only` | `False` | Abortar si hay cualquier CACHE_MISS |
| `--cache-dir` | `.cache/rag` | Directorio de cache |

## Recuperación de evaluación pendiente

Si Phase 2 se omitió (sin API key) o quedó parcial:

```bash
python -m src.evaluation.run_evaluation --latest
python -m src.evaluation.run_evaluation --run-id run_20260512_193621_unknown_878aaf0a
python -m src.evaluation.run_evaluation --latest --poll-batches
python -m src.evaluation.run_evaluation --latest --regenerate-summary
```

## Separación de "medium" vs "final"

`run_experiments.py` no distingue etapas en código. La distinción es operativa:
- Paso 2 (selección de modelo): pocos samples, subset de configs.
  Marcar el run con `experiment_family = "model_selection"` tras ejecutarlo.
- Paso 3 (experimento final): 500+ samples, todas las configs.
  Cae en `main_experiment` por defecto.
