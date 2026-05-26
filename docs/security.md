# Seguridad de la llamada remota

## Propósito

Proteger el endpoint de generación frente a uso no autorizado y manipulación de payload.

## Controles implementados

1. Identidad de cliente con cabecera `X-TFG-Auth`.
2. Integridad de cuerpo con cabecera `X-TFG-Signature`.
3. Validación con comparación en tiempo constante.
4. Respuesta genérica para errores de autenticación.

## Flujo de validación

1. Comprobar presencia de cabeceras.
2. Comprobar prefijo de autenticación.
3. Comprobar clave compartida.
4. Recalcular firma y comparar.
5. Solo entonces ejecutar generación.

## Gestión de claves

1. Clave compartida en `TFG_API_KEY`.
2. Debe coincidir entre cliente y servidor.
3. No se debe versionar en repositorio.

## Endpoints relevantes

1. `/generate` protegido.
2. `/health` de diagnóstico.
3. `/models` y `/active-model` de inspección de estado.

## Limitaciones actuales

1. No hay rotación automatizada de clave.
2. No hay mTLS ni capa de autorización por usuario.

