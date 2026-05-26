# Módulo de recuperación

## Propósito

Seleccionar contexto relevante por consulta para reducir respuestas sin
soporte documental. Proporciona dos estrategias comparables con la misma
interfaz de salida.

## Implementación actual

1. Módulo `src/retrieval/__init__.py`.
2. Dataclass `RetrievalResult` - fragmento recuperado con trazabilidad:
   - `text`, `score`, `rank`, `doc_id`, `source_file`,
   - `chunk_global_id`, `chunk_index_in_doc`,
   - `retrieval_score_type` (`"cosine_similarity"` o `"bm25"`),
   - `reranker_score`, `reranker_score_type`.
3. Clase abstracta `BaseRetriever` con interfaz común:
   - `index(embeddings, texts, metadatas)` - construye el índice.
   - `retrieve(query_embedding, query_text, top_k)` - devuelve fragmentos.
4. `FAISSRetriever` - búsqueda por similitud coseno en índice vectorial denso.
   Métodos: `index()`, `save()`, `load()`, `retrieve()`.
5. `BM25Retriever` - recuperación léxica por frecuencia de términos.
   Métodos: `index()`, `retrieve()`.

## Uso por configuración

- Sufijo `_k` → `BM25Retriever`.
- Sufijo `_s` → `FAISSRetriever`.
- Sufijo `_rr` → recupera `top_k` ampliado (e.g. 25) y recorta a
  `reranker_top_n` (e.g. 5) tras aplicar `CrossEncoderReranker`.

## Funnel retrieval (`_rr`)

La estrategia de embudo en configuraciones con reranker:
1. `BM25Retriever` o `FAISSRetriever` recupera un conjunto amplio (25 candidatos).
2. `CrossEncoderReranker` reordena y recorta a los 5 mejores.
3. El contexto final al LLM tiene el mismo tamaño que en configs sin reranker.

Esto permite al cross-encoder ver más candidatos sin ampliar el contexto final.

## Parámetros prácticos

- Sin reranking: `top_k = 5` efectivo.
- Con reranking: `top_k` de entrada configurable (25) → `reranker_top_n = 5`.
- El preflight del runner ajusta estos valores según el modelo activo.

## Trazabilidad

Todos los campos de `RetrievalResult` se propagan a `SourceInfo` y se
serializan en el log JSON de cada muestra: permite auditar exactamente
qué fragmentos vio el modelo sin reejecutar el pipeline.

## Limitaciones actuales

1. Sin fusión híbrida BM25+FAISS en una configuración única.
2. Sin filtros por metadatos de documento (autor, fecha, sección, etc.).
3. Sensibilidad al tamaño de contexto del modelo remoto cuando `top_k` es alto.
