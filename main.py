"""
Flujo Principal de la Aplicación de Mensajes con NATS

Este microservicio implementa un sistema de mensajería usando NATS como broker de mensajes.
El flujo principal es:

1. Inicio de la Aplicación:
   - Se inicia FastAPI
   - Se conecta a NATS
   - Se registran las suscripciones a los topics

2. Topics NATS:
   - message.create: Para crear nuevos mensajes
   - message.findAll: Para obtener todos los mensajes

3. Procesamiento de Mensajes:
   - Los handlers procesan los mensajes entrantes
   - Se interactúa con la base de datos PostgreSQL de forma asíncrona
   - Se envían respuestas a través de NATS

4. Cierre de la Aplicación:
   - Se cierra la conexión NATS
   - Se liberan los recursos

Dependencias:
- FastAPI: Para el servidor web y health check
- NATS: Para la comunicación asíncrona
- SQLAlchemy: Para la interacción con la base de datos
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from nats.aio.client import Client as NATS

from app.agent.initializer import cleanup_initializer_resources
from app.agent.llm import cleanup_llm_resources
from app.config import get_settings
from app.nats_subscriptions import register_nats_subscriptions

settings = get_settings()
nats = NATS()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await nats.connect(settings.nats_servers_list)
    print(f"✅ Conectado a NATS: {settings.nats_servers_list}")
    await register_nats_subscriptions(nats)

    yield  # <- Aquí la aplicación está corriendo

    # Shutdown
    print("🚪 Cerrando conexión NATS")
    await nats.drain()

    # Cerrar recursos del agente LLM
    print("🚪 Cerrando recursos del agente LLM")
    await cleanup_llm_resources()

    # Cerrar todos los recursos del inicializador (MCP, PostgreSQL, etc.)
    print("🚪 Cerrando todos los recursos del inicializador")
    await cleanup_initializer_resources()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
