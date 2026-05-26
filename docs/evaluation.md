# Evaluación - LLM-as-Judge (OpenAI Responses API)
## Propósito
Medir calidad semántica de las respuestas RAG usando un juez LLM externo.
La evaluación ocurre **fuera del pipeline de generación**, después de que todas las
configuraciones de una ejecución han terminado. No añade latencia a los experimentos.
## Estado actual en código
| Módulo | Contenido |
|---|---|
| `src/evaluation/__init__.py` | Orquestador de evaluación + re-exporta métricas |
| `src/evaluation/schemas.py` | Schema JSON estricto para Structured Outputs + `FAILURE_TYPES` |
| `src/prompts/__init__.py` | `_EVAL_USER_TEMPLATE` con instrucciones de failure attribution |
| `src/evaluation/openai_judge.py` | `OpenAIRagJudge` - Responses API síncrona |
| `src/evaluation/metrics.py` | `recompute_llm_eval_metrics` (incluye 7 métricas de tasa nuevas) |
| `src/evaluation/run_evaluation.py` | Orquestador + CLI + auditorías + resumen |
| `src/evaluation/batch_api.py` | Fallback Batch API para muestras no resueltas |
| `src/evaluation/statistics.py` | Intervalos confianza bootstrap, Wilcoxon, Cohen d |
## Por qué post-run
La evaluación se lanza *después* de que todas las configuraciones terminan porque:
- El juez LLM requiere internet (OpenAI). El pipeline Ollama funciona offline.
- Permite separar latencia del pipeline del tiempo de evaluación.
- Si la evaluación falla (cuota, red), los experimentos ya están guardados y se
  pueden evaluar más tarde sin repetir la generación.
- Los lotes deben ser de una sola configuración para no contaminar el contexto
  del juez.
## Identificadores de muestra
Cada muestra tiene un `eval_item_id` estable:
```
run_20260512_193621_unknown_878aaf0a::baseline_s::0007
```
- `run_id`: unique entre ejecuciones.
- `config_name`: garantiza que los resultados se escriben en el JSON correcto.
- `NNNN`: índice con ceros - permite remapeo sin ambigüedad.
## Ruta primaria - Responses API síncrona
1. `OpenAIRagJudge.evaluate_config_samples()` divide muestras de una config
   en lotes de ≤ 10 (máx. 20).
2. Llama a `client.responses.create()` con `strict=True` y schema
   `rag_eval_batch_result`.
3. Valida respuesta: `received_count`, longitud de `results`, `eval_item_id`
   exactos.
4. En error 429/500/503/timeout/validación, reintenta con backoff exponencial
   + jitter (máx. 3 intentos).
5. Si todos fallan, muestras → `retry_pending`. El JSON se guarda a disco
   tras cada lote.
## Schema de Structured Outputs
Schema: `rag_eval_batch_result`. `additionalProperties: false` en todos los
niveles. `strict: true` en la llamada.

### Campos de calidad (escala 0-100)
`eval_item_id`, `correctness`, `faithfulness`, `answer_relevance`,
`context_support`, `refusal_quality`, `overall` (float 0-100),
`is_refusal`, `is_correct_refusal`, `is_false_refusal`, `has_contradiction` (bool),
`answer_type` (enum: yes_no|entity|date|number|descriptive|unknown).

### Campos de failure attribution (añadidos)
Cada resultado incluye además:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `answer_correct` | bool \| null | ¿La respuesta final es correcta respecto al ground_truth? |
| `context_sufficient` | bool \| null | ¿El contexto recuperado contiene evidencia suficiente para responder? |
| `answer_supported_by_context` | bool \| null | ¿La respuesta está respaldada por el contexto (fidelidad binaria)? |
| `failure_type` | enum | `"none"` \| `"retrieval_failure"` \| `"generation_failure"` \| `"both"` \| `"uncertain"` |
| `judge_summary` | string | Resumen en 1-2 frases del juez sobre el caso |
| `evidence_quotes` | list[string] | Citas literales del contexto que soportan (o desmienten) la respuesta |

**`failure_type` semántica**:
- `none`: contexto suficiente Y respuesta correcta
- `retrieval_failure`: contexto no contiene evidencia para responder
- `generation_failure`: contexto SÍ tiene evidencia pero el LLM falló de todas formas
- `both`: contexto insuficiente Y respuesta incorrecta (no se puede atribuir)
- `uncertain`: el juez no puede determinar con confianza

## Scores - escala 0 a 100
Todos los scores son floats 0.0-100.0. **No se usa la escala 0-1.**
## Métricas de calidad calculadas
`recompute_llm_eval_metrics()` sobre muestras con `eval.status == "completed"`:

### Métricas base (siempre calculadas)
`correctness_mean`, `faithfulness_mean`, `answer_relevance_mean`,
`context_support_mean`, `refusal_quality_mean`, `overall_mean`, `contradiction_rate`,
`refusal_rate`, `correct_refusal_rate`, `false_refusal_rate`, `eval_completion_rate`,
`eval_pending_count`, `eval_failed_count`.

### Métricas de tasa de failure attribution (añadidas)
Calculadas sobre las mismas muestras completadas. Retrocompatibles: muestras sin
los campos nuevos contribuyen 0 a las tasas (no rompen ejecuciones antiguas).

| Métrica | Descripción |
|---------|-------------|
| `answer_accuracy` | % de muestras con `answer_correct == true` |
| `context_sufficiency_rate` | % de muestras con `context_sufficient == true` |
| `faithfulness_rate` | % de muestras con `answer_supported_by_context == true` |
| `retrieval_failure_rate` | % de muestras con `failure_type == "retrieval_failure"` |
| `generation_failure_rate` | % de muestras con `failure_type == "generation_failure"` |
| `combined_failure_rate` | % de muestras con `failure_type == "both"` |
| `uncertain_rate` | % de muestras con `failure_type == "uncertain"` |

Las métricas de rendimiento (latencia, memoria, etc.) se preservan.

### Uso para decisiones de config/modelo
La separación `retrieval_failure_rate` vs `generation_failure_rate` permite argumentar:

- Si `retrieval_failure_rate` es alto en FAISS → el retriever no alcanza los documentos
  necesarios → prueba con reranker o más k
- Si `generation_failure_rate` es alto a pesar de buen `context_support_mean` → el
  modelo falla al sintetizar contexto bueno → use grounded prompt o modelo más grande
- Esto es exactamente lo que Phase 0 mostró: `optimized_s` tiene context_support=78
  (buen contexto recuperado) pero contradiction_rate=0.60 (fallo de generación puro)

## Evaluación pendiente
Si hay muestras `pending`/`retry_pending`:
- No se fabrican scores.
- Medias = solo sobre completadas.
- Cada métrica incluye `n_evaluated` y `n_pending`.
- Estado de config: `partial`.
## Fallback - Batch API
Si `OPENAI_EVAL_ASYNC_BATCH_FALLBACK=true`, las muestras no resueltas se envían
al Batch API. Los trabajos **nunca mezclan configuraciones**. Artefactos en
`logs/runs/<run_id>/evaluation_artifacts/<config>/`.
## Recuperación de pendientes
```bash
python -m src.evaluation.run_evaluation --latest
python -m src.evaluation.run_evaluation --run-id run_20260512_193621_unknown_878aaf0a
python -m src.evaluation.run_evaluation --latest --use-async-batch
python -m src.evaluation.run_evaluation --latest --poll-batches
python -m src.evaluation.run_evaluation --latest --regenerate-summary
```
## Layout de ficheros
```
logs/
  runs/<run_id>/
    run_manifest.json
    experiments/<config>.json          # experimento con eval embedded
    evaluation_artifacts/<config>/     # artefactos Batch API
    summaries/experiment_summary.json  # resumen v2.0 regenerado
  summaries/<run_id>__experiment_summary.json
  index/run_index.jsonl
```
## Variables de entorno relevantes
```ini
OPENAI_API_KEY=sk-...                     # requerido para evaluación
OPENAI_EVAL_MODEL=gpt-5.4-mini            # modelo juez (actual en producción)
OPENAI_EVAL_SYNC_BATCH_SIZE=10
OPENAI_EVAL_SYNC_BATCH_SIZE_MAX=20
OPENAI_EVAL_MAX_SYNC_RETRIES=3
OPENAI_EVAL_RETRY_BASE_SLEEP_SECONDS=5
OPENAI_EVAL_RETRY_MAX_SLEEP_SECONDS=60
OPENAI_EVAL_ASYNC_BATCH_FALLBACK=true
OPENAI_EVAL_ASYNC_POLL_SECONDS=60
OPENAI_EVAL_ASYNC_TIMEOUT_SECONDS=86400
```
`OPENAI_API_KEY` solo requerida para evaluación. El pipeline Ollama es completamente
offline sin ella.
## Logs obsoletos
Los ficheros `logs/experiment_summary_*.json` y `logs/baseline_*.json` de ejecuciones
anteriores al esquema 2.0 no tienen `schema_version="2.0"` y son ignorados por
`generate_charts.py` automáticamente.
