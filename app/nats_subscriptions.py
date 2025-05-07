from nats.aio.client import Client as NATS

from app.handlers import handle_create, handle_find_all


async def register_nats_subscriptions(nc: NATS):
    """
    Registra todas las suscripciones al broker NATS.
    """
    await nc.subscribe("message.create", cb=handle_create)
    await nc.subscribe("message.find.all", cb=handle_find_all)
    print("🎧 Subscripciones registradas: message.create, message.find.all")
