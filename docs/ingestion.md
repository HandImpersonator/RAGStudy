# Módulo de ingesta

## Propósito

Cargar documentos del corpus local y prepararlos para las etapas de chunking
y recuperación.

## Implementación actual

1. Archivo `src/ingestion/__init__.py`.
2. Dataclass `Document` - contenido de texto y metadatos de origen.
3. Dataclass `EvalSample` - muestra de evaluación con `question`,
   `ground_truth`, e identificadores.
4. Clase `DocumentLoader`:
   - `__init__(data_dir, file_prefixes)` - filtra archivos por prefijo.
   - `load_all()` - carga todos los archivos válidos del corpus.
   - `_load_file(filepath)` - carga un archivo individual.
   - `_preprocess(text)` - limpieza ligera de formato.
5. Carga orientada a corpus markdown y texto plano.
6. Limpieza ligera sin reescritura semántica: preserva trazabilidad del
   contenido original con mínima transformación.

## Flujo del módulo

1. Recibe ruta de corpus y lista opcional de prefijos de archivo.
2. Enumera archivos válidos según extensión y prefijos.
3. Lee contenido y aplica limpieza ligera.
4. Construye lista de `Document` con metadatos de origen.
5. Devuelve documentos para fase de chunking.

## Decisiones de diseño

1. Parser simple para preservar trazabilidad del contenido original.
2. Sin dependencias pesadas en la fase de carga.
3. Separación clara entre ingesta, chunking y embeddings.
4. Los metadatos de origen (`source_file`, `doc_id`) se propagan a los `Chunk`
   y de ahí a `SourceInfo` en los logs.

## Limitaciones actuales

1. Sin extracción avanzada de estructura documental (tablas, secciones, etc.).
2. Sin normalización con tokenizador del modelo de generación.
