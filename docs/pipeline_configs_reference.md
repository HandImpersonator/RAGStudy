# Referencia de configuraciones del pipeline

## Nomenclatura

Cada nombre de configuración sigue el patrón:

```
{familia}_{retrieval}[_rr][_grounded]
```

| Segmento      | Valores                  | Significado                        |
|---------------|--------------------------|------------------------------------|
| `familia`     | `baseline`, `optimized`  | Estrategia de chunking             |
| `retrieval`   | `k`, `s`                 | BM25 (`k`) o FAISS (`s`)           |
| `_rr`         | presente / ausente       | Reranker activo                    |
| `_grounded`   | presente / ausente       | Prompt `grounded_sourced`          |

La configuración especial `no_rag` no sigue este patrón: no hay retrieval.

## Tabla completa de configuraciones

| Nº | Nombre                    | Chunking  | Retrieval | Reranker | Prompt           |
|----|---------------------------|-----------|-----------|----------|------------------|
| 1  | `no_rag`                  | -         | -         | -        | direct           |
| 2  | `baseline_k`              | fijo      | BM25      | -        | basic            |
| 3  | `baseline_s`              | fijo      | FAISS     | -        | basic            |
| 4  | `baseline_k_rr`           | fijo      | BM25      | ✓        | basic            |
| 5  | `baseline_s_rr`           | fijo      | FAISS     | ✓        | basic            |
| 6  | `baseline_k_grounded`     | fijo      | BM25      | -        | grounded_sourced |
| 7  | `baseline_s_grounded`     | fijo      | FAISS     | -        | grounded_sourced |
| 8  | `baseline_k_rr_grounded`  | fijo      | BM25      | ✓        | grounded_sourced |
| 9  | `baseline_s_rr_grounded`  | fijo      | FAISS     | ✓        | grounded_sourced |
| 10 | `optimized_k`             | semántico | BM25      | -        | basic            |
| 11 | `optimized_s`             | semántico | FAISS     | -        | basic            |
| 12 | `optimized_k_rr`          | semántico | BM25      | ✓        | basic            |
| 13 | `optimized_s_rr`          | semántico | FAISS     | ✓        | basic            |
| 14 | `optimized_k_grounded`    | semántico | BM25      | -        | grounded_sourced |
| 15 | `optimized_s_grounded`    | semántico | FAISS     | -        | grounded_sourced |
| 16 | `optimized_k_rr_grounded` | semántico | BM25      | ✓        | grounded_sourced |
| 17 | `optimized_s_rr_grounded` | semántico | FAISS     | ✓        | grounded_sourced |

## Pares de comparación (diseño factorial)

### Efecto chunking (baseline → optimized, mismo retrieval y prompt)

| Baseline        | Optimized        | Aislado              |
|-----------------|------------------|----------------------|
| `baseline_k`    | `optimized_k`    | chunking, BM25       |
| `baseline_s`    | `optimized_s`    | chunking, FAISS      |
| `baseline_k_rr` | `optimized_k_rr` | chunking, BM25+RR    |
| `baseline_s_rr` | `optimized_s_rr` | chunking, FAISS+RR   |

### Efecto prompt (basic → grounded_sourced, mismo chunking y retrieval)

| Basic              | Grounded              | Aislado              |
|--------------------|-----------------------|----------------------|
| `baseline_k`       | `baseline_k_grounded` | prompt, BM25 fijo    |
| `baseline_s`       | `baseline_s_grounded` | prompt, FAISS fijo   |
| `optimized_k`      | `optimized_k_grounded`| prompt, BM25 sem.    |
| `optimized_s`      | `optimized_s_grounded`| prompt, FAISS sem.   |

### Efecto reranker (sin rr → con rr, mismo chunking y prompt)

| Sin reranker            | Con reranker             | Aislado               |
|-------------------------|--------------------------|-----------------------|
| `baseline_k`            | `baseline_k_rr`          | reranker, BM25 fijo   |
| `baseline_s`            | `baseline_s_rr`          | reranker, FAISS fijo  |
| `optimized_k`           | `optimized_k_rr`         | reranker, BM25 sem.   |
| `optimized_s`           | `optimized_s_rr`         | reranker, FAISS sem.  |

## DISABLED_CONFIGS

En `scripts/run_experiments.py`:

```python
DISABLED_CONFIGS: frozenset[str] = frozenset({
    # Descomentar para desactivar sin borrar:
    # "baseline_k_grounded",
    # "baseline_s_grounded",
    # ...
})
```

Por defecto todas las configs están activas (frozenset vacío). Comentar líneas
individuales para activar selectivamente.

## Selección por número (CLI)

```bash
# Ejecutar solo configs 1, 2 y 6
python3 scripts/run_experiments.py --configs 1 2 6

# Ejecutar solo baseline basic (1-5)
python3 scripts/run_experiments.py --configs 1 2 3 4 5
```

## Modelos configurables

Definidos en `src/pipeline/__init__.py` o `tfg.env`:

- `RETRIEVAL_MODEL` - modelo de embeddings para FAISS.
- `RERANKER_MODEL` - modelo de cross-encoder para `_rr`.

Valores por defecto:
- `RETRIEVAL_MODEL = "BAAI/bge-base-en-v1.5"`
- `RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"`

## Clave opcional `embed_batch_size` por config

Cada dict de config en `PIPELINE_CONFIGS` admite la clave opcional
`"embed_batch_size"` para sobreescribir el valor global `EMBED_BATCH_SIZE`
definido en `src/pipeline/__init__.py` (actualmente **128**).
`_build_embedder()` lee `config.get("embed_batch_size", EMBED_BATCH_SIZE)`
y lo pasa al constructor de `SentenceTransformerEmbedder`.

```python
# Ejemplo: sobreescribir batch size solo para una config
"optimized_s": {
    "chunking": "semantic",
    "retrieval": "faiss",
    "embed_batch_size": 64,   # ← sobreescribe EMBED_BATCH_SIZE global
    ...
}
```

Si la clave no está presente, se usa `EMBED_BATCH_SIZE`. Cambiar
`EMBED_BATCH_SIZE` afecta a todas las configs que no sobreescriben esta clave.

