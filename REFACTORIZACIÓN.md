# Refactorización del Servicio de Mensajes

## Problema Original

Anteriormente, el sistema requería ejecutar dos servicios FastAPI separados:

1. `uvicorn app.main:app --port 8000` - Servicio principal de mensajes
2. `uvicorn app.llm:app --port 8001` - Servicio LLM para procesamiento de consultas

El servicio principal hacía llamadas HTTP al servicio LLM para generar respuestas de chat, lo que era ineficiente ya que ambos servicios se ejecutaban en el mismo entorno.

## Solución Implementada

Se ha refactorizado el código para eliminar la necesidad de ejecutar dos servicios FastAPI separados. Ahora, el servicio principal utiliza directamente el procesador MCP para generar respuestas de chat.

### Cambios Principales

1. **Eliminación de llamadas HTTP**:

   - Se eliminó la dependencia de `aiohttp` para hacer llamadas HTTP al servicio LLM.
   - Se importa directamente la clase `MCPQueryProcessor` desde `app.llm`.

2. **Gestión del Ciclo de Vida**:

   - Se implementó un patrón singleton para el procesador MCP con la función `get_processor()`.
   - Se agregó código para cerrar correctamente el procesador MCP cuando se detiene la aplicación.

3. **Generación de Tokens**:
   - Se modificó la función `generate_chat_tokens` para usar el procesador MCP y simular la generación de tokens a partir de la respuesta completa.

### Beneficios

- **Eficiencia**: Eliminación de la sobrecarga de comunicación HTTP entre servicios.
- **Simplicidad**: Solo se necesita ejecutar un servicio FastAPI.
- **Mantenibilidad**: Código más limpio y menos propenso a errores.

## Cómo Funciona

1. Cuando se recibe una solicitud para generar una respuesta de chat, se inicializa el procesador MCP si aún no está inicializado.
2. El procesador MCP procesa la consulta y devuelve la respuesta.
3. La respuesta se devuelve al cliente o se procesa para simular la generación de tokens.
4. Cuando se detiene la aplicación, se cierra correctamente el procesador MCP.

## Consideraciones Futuras

- Implementar una verdadera generación de tokens en el procesador MCP.
- Optimizar el uso de memoria y recursos del procesador MCP.
- Agregar manejo de errores más robusto para el procesador MCP.
