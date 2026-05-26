# Módulo de embeddings

## Propósito

Generar vectores para recuperación semántica densa (FAISS) y soportar
reranking cross-encoder en configuraciones `_rr`.

## Implementación actual

1. Módulo `src/embeddings/__init__.py`.
2. Modelo de retrieval configurado en `src/pipeline/__init__.py` (`RETRIEVAL_MODEL`).
3. Modelo de reranking configurado como `RERANKER_MODEL`.

## Modelos de retrieval disponibles

| Modelo                                              | Dims | Estado en código     | Notas                             |
|-----------------------------------------------------|------|----------------------|-----------------------------------|
| `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`  | 384  | **activo (default)** | QA-tuned; rápido; MiniLM destilado |
| `BAAI/bge-base-en-v1.5`                             | 768  | alternativa          | mayor calidad; más lento          |

El modelo activo es `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` (constante
`RETRIEVAL_MODEL` en `src/pipeline/__init__.py`, línea 87).

## Modelos de reranking disponibles

| Modelo                                   | Estado en código     | Notas                              |
|------------------------------------------|----------------------|------------------------------------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2`  | **activo (default)** | rápido; baseline de reranker       |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | alternativa          | mayor calidad; ~2× más lento       |
| `BAAI/bge-reranker-base`                 | alternativa          | arquitectura distinta; alta calidad|

El reranker activo es `cross-encoder/ms-marco-MiniLM-L-6-v2` (constante
`RERANKER_MODEL` en `src/pipeline/__init__.py`, línea 88).

Ambos modelos están entrenados sobre MS MARCO para relevancia de pasajes.

## Batch size de codificación

`EMBED_BATCH_SIZE` en `src/pipeline/__init__.py` controla cuántos chunks se
codifican por pasada GPU/CPU. Valor actual: **256** (servidor dedicado).

Hay dos perfiles documentados en el código:

| Perfil                            | `EMBED_BATCH_SIZE` | Contexto                       |
|-----------------------------------|--------------------|--------------------------------|
| Servidor universitario (RTX 3080 Ti) | 128             | Con Ollama cargado (~1.9 GB VRAM ocupados) |
| **Servidor dedicado ← valor actual** | **256**         | Sin Ollama compartiendo VRAM    |

Por encima de 128-256, el overhead de transferencia de memoria supera la
ganancia de paralelismo en RTX 3080 Ti. Verificado empíricamente -
512 < 256 ≤ 128 en throughput real con bge-base-en-v1.5.

| Batch size | Throughput relativo                                   | Batches para 2.86M chunks (TriviaQA) |
|------------|-------------------------------------------------------|---------------------------------------|
| 32         | lento - CPU default                                   | ~89 436                               |
| 128        | óptimo empírico servidor universitario               | ~22 359                               |
| **256**    | **óptimo empírico servidor dedicado ← valor actual** | ~11 180                               |
| 512        | más lento que 256 (overhead memoria)                  | ~5 590                                |

Para sobreescribir por config individual, añadir la clave `"embed_batch_size"`
al dict de config en `PIPELINE_CONFIGS`.

## Barrido de combinaciones

`scripts/run_retriever_comparison.py` ejecuta todas las combinaciones
`RETRIEVAL_MODELS × RERANKER_MODELS` sobre el subconjunto de configs activas.

## Integración con recuperación

- Configuraciones `_s` usan embeddings densos con FAISS.
- Configuraciones `_k` usan BM25 y no requieren embeddings para recuperar
  (pero sí para reranking si incluyen `_rr`).

## Integración con reranking

1. Configuraciones `_rr` usan cross-encoder para reordenar candidatos.
2. El reranker no cambia el índice de recuperación, solo el orden final.
3. `reranker_score` y `reranker_score_type` se registran en `SourceInfo`
   de cada fragmento para trazabilidad en logs.

## Consideraciones de reproducibilidad

1. El nombre de modelo de retrieval se captura en cada muestra del log JSON.
2. El nombre de modelo de reranker también se registra en `run_manifest.json`.
3. Mantener el mismo modelo de retrieval dentro de cada familia semántica
   para que las comparaciones `_k` vs `_s` sean válidas.

## Limitaciones actuales

1. Coste de indexación sensible a tamaño de corpus (FAISS requiere indexar
   corpus completo antes de la primera ejecución).
2. Dependencia de caché local de modelos para ejecución estable offline.
3. Sin fusión híbrida BM25+FAISS en una sola configuración.


## Propósito

Generar vectores para recuperación semántica densa (FAISS) y soportar
reranking cross-encoder en configuraciones `_rr`.

## Implementación actual

1. Módulo `src/embeddings/__init__.py`.
2. Modelo de retrieval configurado en `src/pipeline/__init__.py` (`RETRIEVAL_MODEL`)
   o en `tfg.env`.
3. Modelo de reranking configurado como `RERANKER_MODEL`.

## Modelos de retrieval disponibles

| Modelo                                              | Dims | Notas                    |
|-----------------------------------------------------|------|--------------------------|
| `BAAI/bge-base-en-v1.5`                             | 768  | alta calidad; default    |
| `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`  | 384  | rápido; QA-tuned         |

## Modelos de reranking disponibles

| Modelo                                   | Notas                        |
|------------------------------------------|------------------------------|
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | mayor calidad; default       |
| `cross-encoder/ms-marco-MiniLM-L-6-v2`  | rápido; baseline de reranker |
| `BAAI/bge-reranker-base`                 | arquitectura alternativa     |

## Batch size de codificación

`EMBED_BATCH_SIZE` en `src/pipeline/__init__.py` controla cuántos chunks se
codifican por pasada GPU/CPU. Valor actual: **128**.

Batch sizes mayores no implican mayor throughput en bge-base-en-v1.5 sobre
RTX 3080 Ti: por encima de 128 el overhead de asignación de memoria supera
la ganancia de paralelismo. Verificado empíricamente - 512 < 256 < 128 en
throughput real.

Servidor universitario: **NVIDIA RTX 3080 Ti (12 GB VRAM)**, CUDA 12.4,
driver 550.163.01.

| Batch size | Throughput relativo                                   | Batches para 2.86M chunks (TriviaQA) |
|------------|-------------------------------------------------------|---------------------------------------|
| 32         | lento - CPU default                                   | ~89 436                               |
| **128**    | **óptimo empírico en RTX 3080 Ti ← valor actual**    | **~22 359**                           |
| 256        | más lento que 128 (overhead memoria)                  | ~11 180                               |
| 512        | más lento que 256 (overhead memoria)                  | ~5 590                                |

Para sobreescribir por config individual, añadir la clave `"embed_batch_size"`
al dict de config en `PIPELINE_CONFIGS`. Si no se especifica, se usa
`EMBED_BATCH_SIZE`.

## Barrido de combinaciones

`scripts/run_retriever_comparison.py` ejecuta todas las combinaciones
`RETRIEVAL_MODELS × RERANKER_MODELS` sobre el subconjunto de configs activas.
Genera tabla LaTeX (`cross_combo_table.tex`) con resultados comparados.

## Integración con recuperación

- Configuraciones `_s` usan embeddings densos con FAISS.
- Configuraciones `_k` usan BM25 y no requieren embeddings para recuperar
  (pero sí para reranking si incluyen `_rr`).

## Integración con reranking

1. Configuraciones `_rr` usan cross-encoder para reordenar candidatos.
2. El reranker no cambia el índice de recuperación, solo el orden final.
3. `reranker_score` y `reranker_score_type` se registran en `SourceInfo`
   de cada fragmento para trazabilidad en logs.

## Consideraciones de reproducibilidad

1. El nombre de modelo de retrieval se captura en cada muestra del log JSON.
2. El nombre de modelo de reranker también se registra en `run_manifest.json`.
3. Mantener el mismo modelo de retrieval dentro de cada familia semántica
   para que las comparaciones `_k` vs `_s` sean válidas.

## Limitaciones actuales

1. Coste de indexación sensible a tamaño de corpus (FAISS requiere indexar
   corpus completo antes de la primera ejecución).
2. Dependencia de caché local de modelos para ejecución estable offline.
3. Sin fusión híbrida BM25+FAISS en una sola configuración.

