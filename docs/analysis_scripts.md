# Scripts de análisis comparativo

Scripts para analizar el efecto de componentes individuales del pipeline.
Todos trabajan sobre los JSONs de experimentos ya ejecutados (`logs/runs/`);
no relajan el pipeline ni llaman al LLM ni a OpenAI.

## `scripts/compare_component_effects.py`

Análisis aislado del efecto marginal de cada componente del pipeline en una
sola pasada sobre todos los runs disponibles.

### Componentes analizados

| Efecto      | Comparación                                      | Variable aislada        |
|-------------|--------------------------------------------------|-------------------------|
| `chunking`  | `baseline_*` vs `optimized_*` (mismo retrieval) | SemanticChunker vs Fixed|
| `reranking` | `*` vs `*_rr` (mismo chunker y retrieval)        | CrossEncoder vs NoReranker |
| `grounding` | `*_basic` vs `*_grounded_sourced`                | Prompt template         |
| `retriever` | `*_k` vs `*_s` (mismo chunker y prompt)          | BM25 vs FAISS           |

### Diseño

- **Solo JSONs de experimentos**, no summaries (los summaries han perdido
  alineación per-sample necesaria para tests pareados).
- **Pasada única** por run: carga cada JSON una vez e indexa por `sample["index"]`.
- **Sin agregación cross-size**: runs por debajo de `--min-samples` se
  descartan antes de llegar al agregador. No mezcla evidence de mini-sweeps
  con campañas completas de 500+ muestras.
- **Retriever usa cap de 45 muestras mínimas** (la campaña model-selection
  que produce pares BM25/FAISS usó 50 muestras; 600 excluiría todas).

### Métricas de salida

Métricas de calidad (juez LLM, 0-100): `correctness`, `faithfulness`,
`answer_relevance`, `context_support`, `overall`.

Métricas de latencia (ms): `retrieval_time_mean_ms`, `reranking_time_mean_ms`,
`generation_time_mean_ms`, `latency_mean_ms`.

Para cada par de componentes: media, IC bootstrap 95%, p-valor Wilcoxon,
Cohen d y diferencia absoluta.

### Uso

```bash
# Todos los efectos, todas las ejecuciones
python3 scripts/compare_component_effects.py

# Solo el efecto de reranking
python3 scripts/compare_component_effects.py --effects reranking

# Filtrar por dataset
python3 scripts/compare_component_effects.py --dataset triviaqa

# Muestras mínimas por run (default 100 para chunking/reranking/grounding)
python3 scripts/compare_component_effects.py --min-samples 200

# Salida en JSON en lugar de texto
python3 scripts/compare_component_effects.py --output-json results.json
```

