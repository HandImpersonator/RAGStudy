# Módulo de prompts

## Propósito

Definir el formato exacto de entrada para el modelo y controlar el nivel de
grounding por configuración. Centraliza todas las plantillas de prompt RAG y
los prompts del juez de evaluación.

## Implementación actual

1. Archivo `src/prompts/__init__.py`.
2. Plantillas activas registradas en `PromptBuilder._TEMPLATES`:
   1. `direct` - pregunta directa sin contexto (control no-RAG).
   2. `basic` - contexto + pregunta sin instrucciones de fidelidad (baseline).
   3. `grounded_sourced` - contexto con etiquetas `[S1]`, `[S2]`… +
      instrucciones de fidelidad equilibradas + citar fuente de cada
      afirmación. Variante optimizada principal.
3. Plantilla archivada (NO registrada, NO usar): `TEMPLATE_GROUNDED`.
   - Igual que `grounded_sourced` pero sin etiquetas de fuente.
   - Retirada porque la regla de abstención era demasiado agresiva, produciendo
     ~50 % de negativas injustificadas y sesgando métricas de hallucination.
4. Separador de contexto `\n---\n`.
5. Plantillas redactadas en inglés (corpus y preguntas también en inglés).
6. `PromptBuilder.build_with_sources()` devuelve también lista de `SourceInfo`
   para trazabilidad completa de fragmentos en logs JSON.

## Clase SourceInfo

`SourceInfo` (dataclass) registra por cada fragmento en el contexto:

- `source_id` - etiqueta visible al LLM: `"S1"`, `"S2"`, etc.
- `chunk_global_id` - ID global estable `"{doc}::chunk::{idx:04d}"`.
- `doc_id`, `source_file`, `chunk_index_in_doc`, `chunker_method`.
- `retrieval_score` / `retrieval_score_type` - score y tipo (cosine / bm25).
- `reranker_score` / `reranker_score_type` - score reranker (None si no aplica).
- `start_char`, `end_char`, `text_chars`, `text_preview`.

Los metadatos internos (rutas, IDs) van solo al log JSON; **no** se exponen al LLM.

## Asignación por configuración

| Configuración              | Prompt             |
|----------------------------|--------------------|
| `no_rag`                   | `direct`           |
| `baseline_k`               | `basic`            |
| `baseline_s`               | `basic`            |
| `baseline_k_rr`            | `basic`            |
| `baseline_s_rr`            | `basic`            |
| `baseline_k_grounded`      | `grounded_sourced` |
| `baseline_s_grounded`      | `grounded_sourced` |
| `baseline_k_rr_grounded`   | `grounded_sourced` |
| `baseline_s_rr_grounded`   | `grounded_sourced` |
| `optimized_k`              | `basic`            |
| `optimized_s`              | `basic`            |
| `optimized_k_rr`           | `basic`            |
| `optimized_s_rr`           | `basic`            |
| `optimized_k_grounded`     | `grounded_sourced` |
| `optimized_s_grounded`     | `grounded_sourced` |
| `optimized_k_rr_grounded`  | `grounded_sourced` |
| `optimized_s_rr_grounded`  | `grounded_sourced` |

> **Nota de diseño:** Las configuraciones `optimized_*` sin sufijo `_grounded`
> usan `basic` (no `grounded_sourced`) para aislar el efecto del chunking
> semántico respecto al prompt. Las variantes `_grounded` combinan ambos
> efectos (chunking semántico + prompt de fidelidad), permitiendo medir el
> efecto del prompt dentro de la familia optimizada.

## Prompts del juez de evaluación (en el mismo módulo)

Los prompts del juez OpenAI LLM están consolidados en `src/prompts/__init__.py`:

- `SYSTEM_PROMPT` - instrucción de sistema para el evaluador.
- `build_user_prompt(samples)` - construye el prompt usuario para un batch.
- Solo expone al juez los campos necesarios: `eval_item_id`, `question`,
  `answer`, `ground_truth`, `contexts`. No filtra texto del prompt ni
  metadatos internos del pipeline.

## Razón de diseño

1. Separar efecto de recuperación del efecto de prompt (diseño factorial).
2. Mantener versión de prompt estable y documentada por rama experimental.
3. Facilitar comparación entre configuraciones con cambios controlados.
4. Evitar abstenciones injustificadas - la regla de `grounded_sourced` usa
   "Refuse ONLY if" en lugar de la regla agresiva del `grounded` archivado.

## Limitaciones actuales

1. Sin conteo de tokens en construcción de prompt; la longitud de contexto se
   controla indirectamente por `top_k` y tamaño de chunk.
2. Las etiquetas `[Sn]` son visibles al LLM en `grounded_sourced` pero su
   uso en la respuesta generada depende de que el modelo las respete.
