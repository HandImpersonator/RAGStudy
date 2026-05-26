# Módulo de chunking

## Propósito

Convertir documentos en fragmentos aptos para recuperación y construcción de contexto.

## Implementación actual

1. Archivo `src/chunking/__init__.py`.
2. Dataclass `Chunk` - representa un fragmento con metadatos completos:
   - `chunk_global_id`: ID estable `"{doc_source}::chunk::{idx:04d}"`.
   - `text`, `doc_source`, `chunk_index`, `start_char`, `end_char`.
3. Estrategias disponibles:
   1. `FixedChunker` - divide por ventana deslizante con tamaño y solapamiento fijos.
   2. `SemanticChunker` - divide por límites de párrafo y agrupa por similitud
      semántica, respetando el tamaño máximo configurado.
4. `BaseChunker` - clase abstracta común con interfaz `chunk(text, doc_source)`.
5. Parámetros activos en el pipeline (todos los grupos):
   - `chunk_size = 512`, `chunk_overlap = 105`
   - Compartidos por `baseline` y `optimized` para aislar el efecto de estrategia.

## Diseño deliberado: mismo tamaño numérico para ambas estrategias

Tanto `FixedChunker` como `SemanticChunker` usan `chunk_size=512` y
`chunk_overlap=105` en todas las 17 configuraciones del pipeline. Esta decisión
es intencional: el experimento compara el **algoritmo de división** (fijo vs
semántico), no el tamaño de ventana. Así la comparativa `baseline` vs `optimized`
aísla el efecto de la estrategia sin contaminarla con un cambio de tamaño.

`SemanticChunker` respeta el máximo de 512 caracteres pero sus fragmentos
reales pueden ser de 250 a 512 caracteres según los límites de párrafo. El
tamaño promedio en producción resulta menor que con `FixedChunker`.

## Uso por configuración

- `baseline_*` usa `FixedChunker`.
- `optimized_*` usa `SemanticChunker`.
- `no_rag` omite este paso.

## Trazabilidad

Los `Chunk` producidos incluyen `start_char` y `end_char`, que se propagan a
`SourceInfo` para auditoría posterior en los logs JSON. El `chunk_global_id`
permite identificar exactamente qué fragmento fue enviado al LLM en cada muestra.

## Justificación experimental

- Mismo tamaño y solapamiento nominales entre ramas para aislar el efecto de estrategia.
- El contraste `baseline` vs `optimized` evita confundir la mejora con un
  cambio de tamaño de chunk.
- Los metadatos de posición (`start_char`, `end_char`) permiten auditar qué
  parte exacta del documento llegó al modelo en cada muestra.

## Limitaciones actuales

1. El conteo efectivo de tokens puede variar según el modelo remoto activo.
2. El `SemanticChunker` depende de la calidad de la segmentación de párrafos
   en cada fuente documental.
