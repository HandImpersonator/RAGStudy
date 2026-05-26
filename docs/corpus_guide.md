# Guía de corpus y datasets

## Propósito

Documentar qué corpus y qué dataset se combinan en cada tipo de experimento.

## Estructura general

1. `data/corpus` para documentos locales del pipeline.
2. `data/eval` para archivos de evaluación listos para cargar.
3. `data/external` para fuentes descargadas y evidencias originales.

## Conjuntos principales

1. Dominio local:
   1. corpus `01_` a `08_`
   2. datasets `sample` y `rag_domain`
2. HotpotQA:
   1. corpus con prefijo `hotpotqa_`
   2. dataset `hotpotqa_eval` (evaluado sobre **1 000 muestras** por defecto)
3. TriviaQA:
   1. corpus en `data/external/evidence/wikipedia`
   2. dataset `triviaqa_eval` (evaluado sobre **500 muestras** por defecto)

El tope de muestras lo aplica automáticamente `DatasetManager.load()`.
HotpotQA usa 1 000 porque su corpus es más corto; TriviaQA usa 500 porque
su corpus de evidencias Wikipedia es muy extenso y 500 muestras son
representativas dentro del presupuesto experimental.

## Regla de higiene experimental

No mezclar corpus de un benchmark con preguntas de otro benchmark dentro de la misma ejecución.

## Relación con runner

`scripts/run_experiments.py` define mapeo explícito dataset a corpus para reducir contaminación de recuperación.

## Aislamiento de cache por dataset

Las etapas `ingestion`, `chunks`, `embeddings` e `indexes` del sistema de
cache son corpus-dependientes: si TriviaQA y HotpotQA usan el mismo corpus,
estas etapas se **comparten** (correcto). Las etapas `retrieval`, `reranking`
y `contexts` incluyen un hash del conjunto de consultas (`query_set_hash`)
en su clave, por lo que quedan **aisladas** automáticamente por dataset.

## Estado futuro planificado

1. Mantener asociación clara dataset corpus dentro de cada `run_id`.
2. Reforzar trazabilidad por muestra con `eval_item_id`.
3. Añadir campo `"dataset"` a los manifests de retrieval/reranking/contexts
   para identificación visual de carpetas en `.cache/rag/`.
