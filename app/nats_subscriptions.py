# app/nats_subscriptions.py
from functools import partial  # 👈

from nats.aio.client import Client as NATS

from app.handlers import handle_message_generate_stream_start  # 👈  nuevo
from app.handlers import (
    handle_chats_by_user,
    handle_message_generate,
    handle_messages_by_chat,
)


async def register_nats_subscriptions(nc: NATS):
    """Registra los handlers en NATS."""
    await nc.subscribe("message.generate", cb=handle_message_generate)
    await nc.subscribe("chats.by.user", cb=handle_chats_by_user)
    await nc.subscribe("messages.by.chat", cb=handle_messages_by_chat)

    # Para streaming usamos partial para inyectar la misma conexión `nc`
    await nc.subscribe(
        "message.generate.streaming.start", cb=partial(handle_message_generate_stream_start, nc)
    )
