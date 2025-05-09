# Microservicio de Mensajes

Este microservicio implementa un sistema de mensajería usando NATS como broker de mensajes y un procesador MCP para generar respuestas de chat.

## Configuración

1. Asegúrate de tener todas las dependencias instaladas:

   ```bash
   pip install -r requirements.txt
   ```

2. Configura las variables de entorno necesarias o usa un archivo `.env` con:
   ```
   DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost/db_name
   DATABASE_MEMORY_URL=postgresql://usuario:contraseña@localhost/db_name
   NATS_SERVERS=nats://localhost:4222
   ```

## Ejecución

Ahora solo necesitas ejecutar un único servicio FastAPI:

```bash
uvicorn app.main:app --port 8000
```

El servicio se conectará a NATS y registrará las suscripciones necesarias. El procesador MCP se inicializará automáticamente cuando se necesite.

## Cambios Recientes

- Refactorización para eliminar la necesidad de ejecutar dos servicios FastAPI separados
- Integración directa con el procesador MCP sin llamadas HTTP intermedias
- Manejo adecuado del ciclo de vida del procesador MCP

## API NATS

El servicio responde a los siguientes temas de NATS:

- `message.generate`: Genera una respuesta completa de chat
- `message.generate.streaming.start`: Inicia la generación de tokens de respuesta
- `chats.by.user`: Devuelve los chats de un usuario
- `messages.by.chat`: Devuelve los mensajes de un chat

## Endpoints HTTP

- `GET /health`: Comprueba el estado del servicio
