# Flujo de barrido de modelos (sweep workflow)

> Para comparar este script con `run_experiments.py` y
> `generate_charts.py`, y entender por qué el sweep **no** puede
> reemplazar al experimento principal aunque ejecute las mismas configs,

## Propsito

Encontrar la mejor combinación de modelo de retrieval × modelo de reranker
para usarla como modelo fijo en las ejecuciones de experimentos principales.
Este barrido es independiente del experimento principal y se ejecuta una sola
vez (o cuando se quiera evaluar nuevos modelos).

## Script

`scripts/run_retriever_comparison.py`

## Modelos barridos

```python
RETRIEVAL_MODELS: list[str] = [
    "BAAI/bge-base-en-v1.5",                             # 768d, alta calidad
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",  # 384d, rápido, QA-tuned
]

RERANKER_MODELS: list[str] = [
    "cross-encoder/ms-marco-MiniLM-L-12-v2",  # alta calidad, ~2× más lento
    "cross-encoder/ms-marco-MiniLM-L-6-v2",   # baseline rápido
    "BAAI/bge-reranker-base",                  # arquitectura alternativa
]
```

Total combinaciones: 2 retrieval × 3 reranker = **6 combinaciones** por config.

## Configuraciones incluidas en el barrido

Por defecto usa `DEFAULT_COMPARISON_CONFIGS` - subconjunto representativo de
las 17 configs activas. Se pueden pasar con `--configs`.

## Ejecución

```bash
# Barrido completo con configs por defecto (con prewarm de cache automático)
python3 scripts/run_retriever_comparison.py

# Barrido con subset de configs
python3 scripts/run_retriever_comparison.py --configs 2 3 4 5

# Dry-run para verificar sin ejecutar
python3 scripts/run_retriever_comparison.py --dry-run

# Limitar muestras por combinación
# (TriviaQA: tope automático 500; HotpotQA: tope automático 1000)
python3 scripts/run_retriever_comparison.py --dataset triviaqa --max-samples 500

# Sin prewarm (útil si prepare_rag_artifacts.py ya se ejecutó)
python3 scripts/run_retriever_comparison.py --no-prewarm-cache

# Solo si todos los artefactos están en caché
python3 scripts/run_retriever_comparison.py --cached-only
```

## Salidas

| Artifact                                                               | Descripción                                   |
|------------------------------------------------------------------------|-----------------------------------------------|
| `logs/runs/<run_id>/`                                                  | JSON de resultados y manifest por combo.      |
| `output/comparison/combo_sweep/<dataset>/<llm_scope>/thesis_compact/` | Tablas LaTeX compactas para la memoria.       |
| `output/comparison/combo_sweep/<dataset>/<llm_scope>/appendix/`        | Evidencias detalladas.                        |
| `output/comparison/combo_sweep/<dataset>/<llm_scope>/raw_evidence/`    | JSON de métricas por combo.                   |

## Relación con el experimento principal

1. El barrido **no modifica** `RETRIEVAL_MODEL` ni `RERANKER_MODEL` en el pipeline.
2. Los resultados del barrido son informativos: se usa la mejor combinación
   como configuración fija en las ejecuciones de `run_experiments.py`.
3. El barrido mide solo métricas de recuperación (MRR, NDCG, latencia).
   La calidad de respuesta final se mide en `run_experiments.py` con Phase 2.

## Cuándo ejecutar

- Al añadir un nuevo modelo de retrieval o reranker al proyecto.
- Al cambiar el corpus de indexación.
- Al sospechar que la combinación por defecto no es óptima para un dataset
  concreto.
- Una vez al inicio del proyecto para justificar la elección de modelos.

## Nota sobre reproducibilidad

Los resultados del barrido deben documentarse en la memoria junto con:
- Tamaño del corpus de prueba usado.
- Dataset de evaluación y número de muestras (TriviaQA: 500 por defecto,
  HotpotQA: 1 000 por defecto).
- Fecha de ejecución y versión de los modelos cacheados.

## Nota sobre cache y prewarm

El runner activa `--prewarm-cache` por defecto. Antes del primer combo,
`_prewarm_combos_before_experiments()` calcula y guarda en `.cache/rag/`
los artefactos deterministas (embeddings, índices, retrieval, reranking).
Si ya existen de una ejecución anterior, todas las etapas son `CACHE_HIT`
y el prewarm termina en segundos. Ver `docs/cache.md` para el detalle del
sistema de cache por etapas.

La salida por pantalla usa `show_progress=True` por defecto: aparecen barras
`tqdm` durante las etapas costosas. Los logs repetitivos per-archivo y
per-modelo se emiten solo en `DEBUG`.
