# Módulo de orquestación

## Propósito

Coordinar todas las etapas del sistema RAG y producir resultados comparables
entre configuraciones. Centraliza la lógica de ensamblaje en un único punto
de entrada.

## Implementación actual

1. Archivo principal `src/pipeline/__init__.py`.
2. Clase central `RAGPipeline`.
3. Resultado por consulta en `PipelineResult`.
4. Mapa de configuraciones en `PIPELINE_CONFIGS` (17 entradas).
5. Mapa numérico `CONFIG_MAP` (claves 1-17) para selección por CLI.

## Configuraciones activas (17)

### Grupo 1 - baseline basic (prompt `direct` / `basic`, chunking fijo)

| Nº | Nombre           | Retrieval | Reranker | Prompt  |
|----|------------------|-----------|----------|---------|
| 1  | `no_rag`         | -         | -        | direct  |
| 2  | `baseline_k`     | BM25      | -        | basic   |
| 3  | `baseline_s`     | FAISS     | -        | basic   |
| 4  | `baseline_k_rr`  | BM25      | ✓        | basic   |
| 5  | `baseline_s_rr`  | FAISS     | ✓        | basic   |

### Grupo 2 - baseline grounded (prompt `grounded_sourced`, chunking fijo)

| Nº | Nombre                   | Retrieval | Reranker | Prompt           |
|----|--------------------------|-----------|----------|------------------|
| 6  | `baseline_k_grounded`    | BM25      | -        | grounded_sourced |
| 7  | `baseline_s_grounded`    | FAISS     | -        | grounded_sourced |
| 8  | `baseline_k_rr_grounded` | BM25      | ✓        | grounded_sourced |
| 9  | `baseline_s_rr_grounded` | FAISS     | ✓        | grounded_sourced |

### Grupo 3 - optimized basic (prompt `basic`, chunking semántico)

| Nº | Nombre           | Retrieval | Reranker | Prompt | Chunking  |
|----|------------------|-----------|----------|--------|-----------|
| 10 | `optimized_k`    | BM25      | -        | basic  | semántico |
| 11 | `optimized_s`    | FAISS     | -        | basic  | semántico |
| 12 | `optimized_k_rr` | BM25      | ✓        | basic  | semántico |
| 13 | `optimized_s_rr` | FAISS     | ✓        | basic  | semántico |

### Grupo 4 - optimized grounded (prompt `grounded_sourced`, chunking semántico)

| Nº | Nombre                    | Retrieval | Reranker | Prompt           | Chunking  |
|----|---------------------------|-----------|----------|------------------|-----------|
| 14 | `optimized_k_grounded`    | BM25      | -        | grounded_sourced | semántico |
| 15 | `optimized_s_grounded`    | FAISS     | -        | grounded_sourced | semántico |
| 16 | `optimized_k_rr_grounded` | BM25      | ✓        | grounded_sourced | semántico |
| 17 | `optimized_s_rr_grounded` | FAISS     | ✓        | grounded_sourced | semántico |

> **Diseño factorial:** `baseline vs optimized` aísla efecto chunking;
> `basic vs grounded_sourced` aísla efecto prompt. Los cruces permiten medir
> interacciones. Los grupos 2 y 4 pueden usarse o desactivarse con
> `DISABLED_CONFIGS` sin modificar código.

## Flujo por consulta

1. Seleccionar configuración por nombre o número (1-17).
2. Si aplica, recuperar contexto: BM25 (`_k`) o FAISS (`_s`).
3. Si la configuración incluye `_rr`, aplicar `CrossEncoderReranker`.
4. Construir prompt con `PromptBuilder` (versión `direct`, `basic` o
   `grounded_sourced`).
5. Llamar al LLM remoto vía `RemoteLLM`.
6. Registrar respuesta, tiempos, `SourceInfo` y metadatos en `PipelineResult`.

## Trazabilidad de chunks

`PipelineResult` incluye `sources: list[SourceInfo]` con por cada fragmento:
- `chunk_global_id`, `doc_id`, `source_file`, `chunk_index_in_doc`.
- `retrieval_score` / `reranker_score`.
- `start_char`, `end_char`, `text_preview`.

Estos datos se serializan en los logs JSON de cada muestra para auditoría
posterior sin reejecutar el pipeline.

## Métricas de tiempo expuestas

`PipelineResult.timings` incluye:

1. `query_embedding_ms`
2. `retrieval_ms`
3. `reranking_ms`
4. `retrieval_total_ms`
5. `prompt_build_ms`
6. `llm_generation_ms`
7. `total_pipeline_ms`

## Integración con ejecución experimental

1. `scripts/run_pipeline.py` - ejecución puntual de una configuración.
2. `scripts/run_experiments.py` - lote completo; evalúa automáticamente
   (Phase 2) al terminar si `OPENAI_API_KEY` está disponible.
3. `DISABLED_CONFIGS: frozenset[str]` en `run_experiments.py` - excluye
   configuraciones sin borrarlas; comentar/descomentar líneas para activar.
4. `scripts/run_retriever_comparison.py` - barrido de combinaciones de
   modelos de retrieval + reranker sobre el subconjunto de configs activas.

## Cache de artefactos deterministas

`RAGPipeline` integra un sistema de cache por etapas (`src/cache.py`)
que evita repetir cómputos costosos cuando los parámetros no cambian:

```
ingestion → chunks → embeddings → indexes → retrieval → reranking → contexts
```

Métodos relevantes de `RAGPipeline`:

- `attach_cache(cache, query_ids, cached_only)` - vincula el `CacheManager`
  antes de llamar a `build_index()`.
- `build_index()` - comprueba cada etapa en orden; usa artefacto de cache si
  el manifest coincide, o recalcula y guarda si hay MISS.
- `flush_cache()` - escribe `_pending_retrieval`, `_pending_reranking` y
  `_pending_contexts` al disco tras el bucle de consultas.

El pre-cómputo manual se realiza con `scripts/prepare_rag_artifacts.py`.
El prewarm automático ocurre antes del bucle en `run_experiments.py` y
`run_retriever_comparison.py` (flag `--prewarm-cache`, activo por defecto).

Ver `docs/cache.md` para el diagrama completo de etapas y claves.

## Barras de progreso

`RAGPipeline._show_progress = True` por defecto. Cuando está activo:

- Ingestion: barra `tqdm` sobre los archivos del corpus.
- Chunking: barra `tqdm` sobre los documentos.
- Embeddings: `show_progress_bar=True` pasado a `SentenceTransformer.encode()`.
- Retrieval+reranking en prewarm: barra `tqdm` sobre las consultas.

Los logs per-archivo y per-modelo se emiten en `DEBUG` para no competir
con las barras.

## Limitaciones actuales

1. Sin fusión híbrida BM25+FAISS en una sola configuración.
2. Sin filtros por metadatos de documento en la recuperación.
3. Sensibilidad a tamaño de contexto del modelo remoto cuando `top_k` es alto.
