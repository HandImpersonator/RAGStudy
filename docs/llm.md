# Módulo de integración LLM

## Propósito

Gestionar la llamada remota de generación y devolver una respuesta trazable para
cada consulta. El cliente firma cada petición y registra el modelo activo real.

## Implementación actual

1. Módulo cliente `src/llm/__init__.py` - clase activa `RemoteLLM`.
2. Servidor `scripts/llm_server.py` - servidor FastAPI que envuelve Ollama.
3. Endpoint `POST /generate` en el servidor.
4. Autenticación con cabecera `X-TFG-Auth` (clave compartida).
5. Integridad de petición con `X-TFG-Signature` (HMAC-SHA256 sobre el cuerpo).

## Contrato de respuesta

Cada llamada a `RemoteLLM.generate()` devuelve un `LLMResponse` con:

1. `text` - texto generado
2. `prompt_tokens` - tokens del prompt enviado
3. `completion_tokens` - tokens generados
4. `latency_ms` - latencia de red + inferencia
5. `model_requested` - nombre de modelo configurado en el cliente
6. `actual_model` - modelo activo real detectado en el servidor

El pipeline usa `actual_model` para etiquetar cada muestra en el log JSON.
Si el servidor cambia de modelo entre peticiones, el log refleja el modelo real.

## Servidor LLM (`scripts/llm_server.py`)

1. FastAPI sobre Uvicorn.
2. Reenvía el prompt a Ollama (localhost:11434) con los parámetros de la config.
3. Exponible en red local; protegido por HMAC para evitar uso no autorizado.
4. El endpoint `GET /health` permite al cliente verificar conectividad y nombre
   del modelo activo antes de lanzar experimentos.

## Operación diaria

1. El operador cambia modelo en el servidor con `ollama run <nombre>`.
2. El cliente no necesita reconfiguración: lee `actual_model` en cada respuesta.
3. Temperatura y longitud máxima se controlan en `PIPELINE_CONFIGS`, no en el servidor.

## Modelos usados en experimentos

| Fase             | Modelo(s)                                  | Notas                                      |
|------------------|--------------------------------------------|--------------------------------------------|
| Barrido cribado  | llama3.2, mistral:7b, llama3:8b (variados) | Paso 1 - selección retriever × reranker    |
| Selección modelo | llama3.2, mistral:7b, llama3:8b            | Paso 2 - 50 muestras por config            |
| Experimentos finales | modelo seleccionado                        | Paso 3 - 500+ muestras por config          |
| Juez evaluador   | GPT-5.4-mini (OpenAI)                      | Phase 2 — evaluación semántica             |

## Seguridad

Ver [security.md](security.md) para el modelo de amenazas completo.

1. Clave compartida en `TFG_API_KEY` / `tfg.env`.
2. Firma HMAC-SHA256 sobre el cuerpo de cada petición.
3. Errores de autenticación devuelven 401 genérico (sin detallar el motivo).

## Variables de entorno

```ini
TFG_SERVER_URL=http://<servidor>:<puerto>   # URL del servidor LLM
TFG_API_KEY=<clave_compartida>              # clave de autenticación
TFG_DEBUG_MODE=                             # activa logging extra en cliente
```

Cargadas desde `tfg.env` o variables de entorno del sistema.
Ver `src/config_loader.py`.

## Limitaciones actuales

1. Dependencia de disponibilidad del servidor remoto.
2. Variación de latencia según carga del modelo activo.
3. Sin soporte de streaming nativo - la respuesta llega completa.
