"""
Suscripciones NATS

Este módulo registra los handlers para los diferentes topics de NATS.
"""

from nats.aio.client import Client as NATS

from app.handlers import (
    handle_chats_by_user,
    handle_message_generate,
    handle_message_generate_streaming,
    handle_messages_by_chat,
)


async def register_nats_subscriptions(nc: NATS):
    """
    Registra los handlers para los diferentes topics de NATS.
    """
    print("🎧 Subscripciones registradas: message.create, message.find.all")
    await nc.subscribe("message.generate", cb=handle_message_generate)
    await nc.subscribe("message.generate.streaming", cb=handle_message_generate_streaming)
    await nc.subscribe("chats.by.user", cb=handle_chats_by_user)
    await nc.subscribe("messages.by.chat", cb=handle_messages_by_chat)
