# Módulo de reranking

## Propósito

Reordenar candidatos recuperados para mejorar la calidad de contexto que llega
al prompt final, aplicando un cross-encoder más preciso (pero más lento) que
el retriever inicial.

## Implementación actual

1. Módulo `src/reranking/__init__.py`.
2. Clase `CrossEncoderReranker` - reranker basado en cross-encoder.
3. Clase `NoReranker` - pass-through; conserva el orden del retriever.
4. Constante `RERANKER_MODEL` en `src/pipeline/__init__.py` (línea 88) -
   punto único de configuración.

## Modelos de reranking disponibles

| Modelo                                      | Estado en código     | Velocidad    | Notas                              |
|---------------------------------------------|----------------------|--------------|------------------------------------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2`     | **activo (default)** | rápido       | baseline del reranker; MiniLM 6 capas |
| `cross-encoder/ms-marco-MiniLM-L-12-v2`    | alternativa          | ~2× más lento| MiniLM 12 capas; mayor calidad      |
| `BAAI/bge-reranker-base`                    | alternativa          | variable     | arquitectura distinta (BGE)         |

Todos están entrenados sobre MS MARCO para relevancia de pasajes (par query/passage).
El reranker activo es `cross-encoder/ms-marco-MiniLM-L-6-v2` (línea 88 del pipeline).

## Barrido de modelos

`scripts/run_retriever_comparison.py` ejecuta combinaciones de retrieval ×
reranker sobre el subconjunto de configs seleccionadas:

```python
RETRIEVAL_MODELS = [
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
]
RERANKER_MODELS = [
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "BAAI/bge-reranker-base",
]
```

Genera artefactos bajo:
```
output/comparison/combo_sweep/<dataset>/<llm_scope>/
    thesis_compact/        ← tablas compactas para la memoria
    appendix/              ← evidencias detalladas
    raw_evidence/          ← JSON de métricas por combo
    diagnostics_per_combo/ ← (con --with-diagnostics)
```

## Papel en la matriz experimental

1. Comparaciones `*` vs `*_rr` miden coste-beneficio del reranker.
2. El diseño factorial permite medir el efecto tanto en `baseline` como en
   `optimized`, y tanto con `basic` como con `grounded_sourced`.
3. Pares de aislamiento:
   - `baseline_k` vs `baseline_k_rr` - efecto reranker puro, BM25.
   - `baseline_s` vs `baseline_s_rr` - efecto reranker puro, FAISS.
   - `optimized_k` vs `optimized_k_rr` - efecto reranker con chunking semántico.

## Estrategia de embudo (`_rr`)

1. `BM25Retriever` o `FAISSRetriever` recupera 25 candidatos (`top_k = 25`).
2. `CrossEncoderReranker` evalúa cada par (query, chunk) conjuntamente.
3. Se retienen los 5 mejores (`reranker_top_n = 5`).
4. El contexto final al LLM tiene el mismo tamaño que en configs sin reranker.

El cross-encoder ve más candidatos sin ampliar el contexto final.

## Parámetros de recuperación

- Sin reranking: `top_k = 5` (efectivo final).
- Con reranking: `top_k = 25` de entrada → `reranker_top_n = 5` al LLM.

## Métricas relacionadas

1. Impacta `reranking_ms` y `retrieval_total_ms`.
2. Puede afectar `faithfulness`, `context_support` y `correctness` en Phase 2.
3. El campo `reranker_score_type = "cross_encoder_logit"` identifica los logits
   crudos (~-11 a +11) del cross-encoder en los logs; `"pass_through"` para NoReranker.

## Limitaciones actuales

1. Paso costoso en tiempo para lotes grandes sin cache precalculada.
2. El cross-encoder evalúa cada par (query, chunk) por separado sin reutilizar
   representaciones intermedias.
