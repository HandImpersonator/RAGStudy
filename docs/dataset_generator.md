# Generador de dataset de dominio

## Propósito

Crear un conjunto de evaluación local a partir del corpus técnico del proyecto.

## Implementación actual

1. Script `scripts/generate_dataset.py`.
2. Entrada principal en `data/corpus`.
3. Salida principal en `data/eval/rag_domain_eval.json`.
4. Enfoque basado en plantillas, sin dependencia de LLM externo.

## Flujo de generación

1. Leer documentos del corpus.
2. Detectar secciones útiles.
3. Construir preguntas con plantillas temáticas.
4. Extraer respuesta y contexto de referencia.
5. Guardar triples en JSON.

## Auto-generación de splits TriviaQA / HotpotQA

`DatasetManager.load()` genera automáticamente los ficheros de evaluación
si no existen en `data/eval/`:

- `triviaqa_eval.json` - se construye desde
  `data/external/qa/wikipedia-dev.json` + `data/external/evidence/wikipedia/`.
  Si el JSON no está extraído, se intenta descomprimir el `.tar.gz`.
- `hotpotqa_eval.json` - se construye desde el archivo de HotpotQA
  descargado en `data/external/`.

Este mecanismo hace que `--dataset triviaqa` funcione out-of-the-box
sin ejecutar `generate_dataset.py` manualmente.

## Tope automático de muestras (datasets grandes)

Para no sobrepasar el presupuesto experimental (latencia LLM + coste del
juez OpenAI), `DatasetManager.load()` aplica un tope automático:

| Dataset          | Tope por defecto |
|------------------|-----------------|
| `triviaqa`       | 1000            |
| `triviaqa_eval`  | 1000            |
| `hotpotqa`       | 1 000           |
| `hotpotqa_eval`  | 1 000           |

- Si `max_samples == 0` (todos) → se recorta al tope con aviso `INFO`.
- Si `max_samples > cap` → ídem.
- Si `max_samples ≤ cap` → se respeta el valor del usuario.
- HotpotQA usa 1 000 porque su corpus es más corto que el de TriviaQA.
- Otros datasets (`rag_domain`) no tienen tope.

El tope se aplica también al construir el fichero JSON: el builder recibe
`max_samples` explícitamente para que el fichero generado no contenga
más entradas de las que se van a usar.

## Ventajas del enfoque actual

1. Reproducible sin red.
2. Rápido para iteración técnica.
3. Compatible con `DatasetManager`.

## Limitaciones actuales

1. Variedad lingüística menor que la de preguntas humanas.
2. Calidad del triple depende de reglas de extracción.

## Estado futuro planificado

1. Mantener este dataset para validación rápida.
2. Priorizar evaluación LLM post ejecución para medir calidad semántica real de respuestas.
