# Variables sensibles de servidor

## Propósito

Listar configuración sensible necesaria para cliente y servidor remoto.

## Variables compartidas

1. `TFG_API_KEY`
2. `TFG_SERVER_URL`
3. `TFG_DEBUG_MODE`

Estas variables se gestionan desde entorno o `tfg.env`.

## Variables de servidor

1. host y puerto de FastAPI
2. URL local de Ollama
3. nombre de cabeceras de autenticación

## Reglas de despliegue

1. Nunca usar claves de ejemplo en ejecución real.
2. Mantener `TFG_DEBUG_MODE=0` fuera de entorno de desarrollo.
3. Verificar salud de servidor antes de campañas largas.

## Checklist mínimo

1. clave compartida cargada en cliente y servidor
2. endpoint `/health` operativo
3. modelo activo cargado en Ollama
4. conectividad cliente servidor validada

