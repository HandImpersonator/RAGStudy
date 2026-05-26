# Capa de datos

## Propósito

Gestionar fuentes de corpus y conjuntos de evaluación que alimentan el experimento.

## Rutas clave

1. `data/corpus/` - documentos indexables (markdown y texto plano).
2. `data/eval/` - archivos de evaluación parseados a `EvalSample`.
3. `data/external/` - descargas y evidencias externas (TriviaQA Wikipedia).

## Implementación actual

1. Archivo `src/dataset_manager.py`.
2. Dataclass `DatasetConfig` - registro de un dataset: rutas, subconjunto,
   número máximo de muestras, corpus asociado.
3. Clase `DatasetManager`:
   - `list_available()` - lista los datasets registrados.
   - `is_cached(dataset_name)` - comprueba si ya está descargado.
   - `load(dataset_name, max_samples)` - carga `EvalSample` desde disco.
   - `download(dataset_name)` - descarga el dataset si no está en caché.
   - `load_or_download(dataset_name)` - combina ambas operaciones.
   - `load_corpus_documents()` - carga documentos del corpus asociado.
4. Datasets registrados:
   - `sample` - dataset de prueba local.
   - `rag_domain` - preguntas sobre conceptos técnicos del proyecto.
   - `wikipedia` - evidencias Wikipedia (TriviaQA).
   - `hotpotqa_eval` - subset HotpotQA.
   - `triviaqa_eval` - subset TriviaQA.

## Mapeo dataset → corpus

| Dataset        | Corpus indexado                              |
|----------------|----------------------------------------------|
| `sample`       | `data/corpus/01_*.md`…`08_*.md`              |
| `rag_domain`   | `data/corpus/01_*.md`…`08_*.md`              |
| `hotpotqa`     | `data/corpus/hotpotqa_*.md`                  |
| `triviaqa`     | `data/external/evidence/wikipedia/`          |

El mapeo explícito en código evita mezcla de corpus entre datasets.

## Trazabilidad por ejecución

- El `run_id` y el `eval_item_id` por muestra son estables entre
  ejecución y evaluación Phase 2: permiten unir respuestas generadas
  y resultados del juez LLM sin reejecutar el pipeline.
- El dataset usados se registra en `run_manifest.json` de cada ejecución.

## Limitaciones actuales

1. Para campañas amplias hay que descargar los datasets externos con
   `python3 scripts/download_corpus.py` antes de ejecutar el runner.
2. Sin control de versión de dataset; se usa el archivo en caché tal como está.
