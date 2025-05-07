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

from app.nats_subscriptions import register_nats_subscriptions

nats = NATS()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await nats.connect("nats://localhost:4222")
    print("✅ Conectado a NATS")
    await register_nats_subscriptions(nats)

    yield  # <- Aquí la aplicación está corriendo

    # Shutdown
    print("🚪 Cerrando conexión NATS")
    await nats.drain()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
