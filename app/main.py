import asyncio

from fastapi import FastAPI
from nats.aio.client import Client as NATS

from app.nats_subscriptions import register_nats_subscriptions

nats = NATS()
app = FastAPI()


@app.on_event("startup")
async def startup():
    await nats.connect("nats://localhost:4222")
    print("✅ Conectado a NATS")
    await register_nats_subscriptions(nats)


@app.on_event("shutdown")
async def shutdown():
    print("🚪 Cerrando conexión NATS")
    await nats.drain()


@app.get("/health")
async def health():
    return {"status": "ok"}
