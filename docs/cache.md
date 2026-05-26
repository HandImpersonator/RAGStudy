# Cache de artefactos deterministas

## Propósito

Precomputar y reutilizar artefactos costosos del pipeline (embeddings,
índices FAISS, retrieval, reranking) de forma que los experimentos con
distintos modelos LLM no repitan trabajo ya hecho.

## Módulo

`src/cache.py` - clase `CacheManager`.

## Las 7 etapas y sus claves

```
ingestion  → sha256(rutas de archivo + hashes de contenido)[:16]
chunks     → sha256(ingestion_key + chunker + chunk_size + overlap)[:16]
embeddings → sha256(chunks_key + modelo_embedder)[:16]
indexes    → sha256(embeddings_key + tipo_retriever)[:16]
retrieval  → sha256(index_key + top_k + retrieval_model + query_set_hash)[:16]
reranking  → sha256(retrieval_key + reranker_model + reranker_top_n)[:16]
contexts   → sha256(reranking_key + prompt_version)[:16]
```

Cada etapa hereda la huella de la anterior. Un cambio en cualquier
parámetro upstream invalida automáticamente todos los artefactos
downstream.

## Estructura en disco

```
.cache/rag/
├── ingestion/
│   └── <key16>/
│       ├── manifest.json
│       └── documents.jsonl
├── chunks/
│   └── <key16>/
│       ├── manifest.json
│       └── chunks.jsonl
├── embeddings/
│   └── <key16>/
│       ├── manifest.json
│       └── embeddings.npy
├── indexes/
│   └── <key16>/
│       ├── manifest.json
│       ├── faiss.index   (FAISS) o bm25.pkl (BM25)
│       └── texts.jsonl
├── retrieval/
│   └── <key16>/
│       ├── manifest.json
│       ├── retrieved_top_k.jsonl
│       └── timings.json          # opcional, ver sección "Timings sidecar"
├── reranking/
│   └── <key16>/
│       ├── manifest.json
│       ├── reranked_top_n.jsonl
│       └── timings.json          # opcional
└── contexts/
    └── <key16>/
        ├── manifest.json
        ├── contexts.jsonl
        └── timings.json          # opcional
```

Cada `manifest.json` contiene los parámetros exactos que generaron el
artefacto. Al cargar, se validan los manifests; cualquier discrepancia
produce un `CACHE_MISS` y el artefacto se recalcula.

> **Campo `dataset` en etapas tardías.** Los manifests de `retrieval/`,
> `reranking/` y `contexts/` incluyen un campo `"dataset": "<nombre>"`
> (por ejemplo `"triviaqa"`) que identifica visualmente qué dataset generó
> cada carpeta dentro de `.cache/rag/<dataset>/`. Este campo es puramente
> informativo (no forma parte del fingerprint que determina el hit/miss) y
> se omite en las etapas `ingestion`, `chunks`, `embeddings` e `indexes`
> porque éstas pueden ser compartidas por varios datasets.

## Timings sidecar (`timings.json`)

A partir de v2.x, `prepare_rag_artifacts.py` y `RAGPipeline.run_batch()`
escriben un fichero `timings.json` junto a cada artefacto de
`retrieval/`, `reranking/` y `contexts/` con las métricas medidas
durante el cómputo original. Cuando un experimento posterior carga la
caché, el pipeline restaura esos números en `PipelineResult.timings`
para que el log final tenga la misma forma que una ejecución *live*.

Esquema:

```json
{
  "stage": "retrieval",
  "n_queries": 500,
  "config": { "top_k": 25, "index": "<key16>", "query_set": "<key16>" },
  "elapsed_ms_per_query": {
    "<query_id>": {
      "query_embedding_ms": 12.4,
      "retrieval_ms":       824.3,
      "memory_peak_mb":     1024.5
    }
  },
  "elapsed_ms_total": {
    "query_embedding_ms": 6234.0,
    "retrieval_ms":       412573.0
  }
}
```

Métricas por etapa:

| Etapa       | Claves                                                            |
| ----------- | ----------------------------------------------------------------- |
| `retrieval` | `query_embedding_ms`, `retrieval_ms`, `memory_peak_mb`            |
| `reranking` | `reranking_ms`, `memory_peak_mb`                                  |
| `contexts`  | `context_selection_ms`, `memory_peak_mb`                          |

`prompt_build_ms` y `llm_generation_ms` **no** se cachean: el LLM se
invoca siempre en vivo y cachear esos tiempos sería engañoso. La
metadata del `PipelineResult` incluye `timings_source` indicando si
cada métrica viene de la caché (`"cached"`) o se midió en vivo
(`"live"`); `"missing"` cuando la caché es de un prewarm anterior a la
introducción del sidecar.

`memory_peak_mb` se obtiene con `getrusage(RUSAGE_SELF).ru_maxrss/1024`
(Linux) y refleja el pico observado **hasta** el final de esa consulta;
es monotónico para todo el proceso, no un delta por query.

**Limitación documentada:** los números reflejan el hardware y la carga
del prewarm, no de la ejecución actual. Si los runs experimentales se
ejecutan en la misma máquina con la misma carga (caso por defecto del
proyecto, post-migración al servidor), el sesgo es despreciable.
produce un `CACHE_MISS` y el artefacto se recalcula.

## Aislamiento por dataset

Las etapas `ingestion`, `chunks`, `embeddings` e `indexes` dependen
solo del corpus (archivos en disco). Si TriviaQA y HotpotQA usan el
mismo corpus, estas etapas se **comparten** entre datasets - correcto,
porque los artefactos son idénticos.

Las etapas `retrieval`, `reranking` y `contexts` incluyen
`query_set_hash = sha256(sorted(query_ids))` en su clave. Como las
preguntas de cada dataset son distintas, estas etapas quedan
**aisladas** automáticamente sin ninguna configuración adicional.

## Evicción automática

Cada etapa tiene un cap distinto, dimensionado al diseño experimental
(hasta 17 configuraciones que comparten corpus + chunker + modelo de
embeddings):

| Etapa        | Cap | Tamaño aprox/entrada | Justificación                                      |
| ------------ | --- | -------------------- | -------------------------------------------------- |
| `ingestion`  | 8   | ~1 GB                | 1 corpus por dataset + margen para rollbacks       |
| `chunks`     | 12  | ~3-4 GB              | fixed + semantic + versiones de parámetros         |
| `embeddings` | 16  | ~9 GB                | 2 modelos × 2 chunkers + margen                    |
| `indexes`    | 32  | ~6-10 GB             | BM25×2 chunkers + FAISS×2 chunkers×2 modelos       |
| `retrieval`  | 128 | ~10 MB               | una entrada por (chunker, retriever, modelo, k)    |
| `reranking`  | 128 | ~10 MB               | una por (retrieval_key, reranker, top_n)           |
| `contexts`   | 128 | ~25 MB               | una por configuración completa

Los caps generosos en las tres etapas pequeñas son **críticos**: con
`cap=2` (valor original, ahora reemplazado por 128) un barrido de 17
configuraciones evicta sus propias salidas intermedias y obliga a
recomputar retrieval (~1.5 h por configuración BM25 a 500 queries). Como
cada entrada ocupa pocos MB, mantener 128 ocupa <1 GB.

La evicción se ejecuta automáticamente al escribir un nuevo artefacto;
se elimina la entrada más antigua por `mtime` del `manifest.json`.

Límite configurable por etapa:

```python
cache = CacheManager(max_entries={"embeddings": 6, "contexts": 64})
```

## Prewarm (`prepare_rag_artifacts.py`)

```bash
# Precalcular todos los artefactos para triviaqa
python3 scripts/prepare_rag_artifacts.py \
    --dataset triviaqa \
    --chunkers fixed semantic \
    --retrievers bm25 faiss \
    --retrieval-models BAAI/bge-base-en-v1.5 \
                       sentence-transformers/multi-qa-MiniLM-L6-cos-v1 \
    --rerankers cross-encoder/ms-marco-MiniLM-L-6-v2 \
                cross-encoder/ms-marco-MiniLM-L-12-v2 \
                BAAI/bge-reranker-base \
    --top-k 25 \
    --reranker-top-n 5 \
    --max-samples 500
```

El script itera sobre todos los combos `chunker × retriever ×
retrieval_model × reranker` sin invocar al LLM. Al terminar, los
experimentos LLM consumen los contextos precalculados con coste mínimo.

## Fast-path y verificación por etapa

`prepare_rag_artifacts.py` ejecuta la lógica siguiente para cada combo:

1. **Pre-carga por etapa**: carga en memoria `retrieved_top_k.jsonl`,
   `reranked_top_n.jsonl` y `contexts.jsonl` de forma independiente
   (`CACHE_PRE_LOAD retrieval/reranking/contexts`).
2. **Detección de queries ausentes**: compara los `query_id` presentes
   en el buffer de contextos con el conjunto completo de queries. Solo
   las queries que faltan se procesan en el bucle.
3. **Fast-path completo**: si todos los `query_id` están en el buffer de
   contextos (`missing_pairs` vacío), retorna de inmediato con
   `CACHE_HIT … all N queries in contexts cache, skipping query loop`.
4. **Relleno incremental**: si un fichero JSONL existe pero sólo contiene
   M < N queries (carrera interrumpida), el bucle procesa únicamente las
   N−M ausentes y `flush_cache()` escribe el fichero completo al terminar.

Este diseño garantiza que una interrupción no exige recomputar desde cero:
basta reejecutar el mismo comando y el script continúa donde se quedó.

## Uso desde los runners

```bash
# Con cache + prewarm automático (default)
python3 scripts/run_experiments.py --dataset triviaqa

# Sin prewarm (útil si ya se ejecutó prepare_rag_artifacts.py)
python3 scripts/run_experiments.py --dataset triviaqa --no-prewarm-cache

# Solo si todo está en caché (aborta en cualquier MISS)
python3 scripts/run_experiments.py --dataset triviaqa --cached-only

# Sin cache en absoluto
python3 scripts/run_experiments.py --dataset triviaqa --no-use-cache
```

## GPU y batching durante el prewarm

`SentenceTransformer.encode()` detecta CUDA automáticamente vía PyTorch y
además recibe `device="cuda"` explícito para evitar fallback silencioso a CPU.
En el servidor universitario (RTX 3080 Ti, 12 GB VRAM), los embeddings
se computan en GPU. El parámetro `EMBED_BATCH_SIZE` (por defecto **128**) en
`src/pipeline/__init__.py` controla el tamaño de lote.

128 es el punto óptimo empíricamente verificado en RTX 3080 Ti con
bge-base-en-v1.5: batch sizes mayores (256, 512) producen menor throughput
por overhead de transferencia de memoria. Para el corpus TriviaQA (~2.86M
chunks), esto supone ~22 359 pasadas GPU. El parámetro puede sobreescribirse
por config individual con la clave `"embed_batch_size"` en el dict de
configuración.

## Logs esperados (nivel INFO)

```
CACHE_HIT  [ingestion]  key=a3f1c2d4…  (0.01 s)
CACHE_MISS [chunks]     key=7b3e9f12…  (calculando…)
CACHE_HIT  [embeddings] key=9c1a4b7e…  (0.05 s)
CACHE_HIT  [indexes]    key=2e8f3d9c…  (0.03 s)
CACHE_MISS [retrieval]  key=5a2b6c8e…  (calculando…)
…
CACHE_HIT [optimized_s_rr] - all stages cached, skipping query loop (0.12 s)
```

