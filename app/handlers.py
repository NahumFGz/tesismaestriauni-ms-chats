"""
Manejadores de Mensajes NATS - Modo Demo

Estos handlers están diseñados para simular el comportamiento básico de un sistema de chat
sin conexión a base de datos. Útil para pruebas de integración con el gateway y ver
cómo se comportan las respuestas y el streaming por NATS.
"""

import asyncio
import json
import uuid

from nats.aio.msg import Msg


async def handle_message_generate(msg: Msg):
    """Simula la generación de una respuesta completa para un mensaje"""
    payload = json.loads(msg.data.decode())
    print(f"📨 [generate] Recibido: {payload}")

    chat_uuid = payload["data"].get("chat_uuid", str(uuid.uuid4()))
    content = payload["data"]["content"]
    response_text = content + " → respuesta demo completa"

    response = {
        "chat_uuid": chat_uuid,
        "content": response_text,
    }

    await msg.respond(json.dumps(response).encode())


async def handle_message_generate_streaming(msg: Msg):
    """Simula la generación de una respuesta palabra por palabra"""
    payload = json.loads(msg.data.decode())
    print(f"📨 [generate.streaming] Recibido: {payload}")

    chat_uuid = payload["data"].get("chat_uuid", str(uuid.uuid4()))
    content = payload["data"]["content"]
    respuesta = content + " → tokens de respuesta demo"
    tokens = respuesta.split()

    full_message = ""

    for i, token in enumerate(tokens):
        full_message += token + " "
        await asyncio.sleep(0.2)  # Simula delay entre tokens

        await msg.respond(
            json.dumps(
                {
                    "chat_uuid": chat_uuid,
                    "token": token,
                    "is_complete": False,
                    "full_message": full_message.strip(),
                }
            ).encode()
        )

    # Señal de finalización
    await msg.respond(
        json.dumps(
            {
                "chat_uuid": chat_uuid,
                "token": "",
                "is_complete": True,
                "full_message": full_message.strip(),
            }
        ).encode()
    )


async def handle_chats_by_user(msg: Msg):
    """Simula la devolución de una lista de chats de prueba"""
    print(f"📨 [chats.by.user] Recibido")

    chats = [
        {"chat_uuid": str(uuid.uuid4()), "updated_at": "2025-05-07T10:00:00Z"},
        {"chat_uuid": str(uuid.uuid4()), "updated_at": "2025-05-06T12:00:00Z"},
    ]
    await msg.respond(json.dumps(chats).encode())


async def handle_messages_by_chat(msg: Msg):
    """Simula la devolución de mensajes de un chat de prueba"""
    print(f"📨 [messages.by.chat] Recibido")

    messages = [
        {"id": 1, "sender_type": "USER", "content": "Hola"},
        {"id": 2, "sender_type": "SYSTEM", "content": "Hola, ¿cómo estás?"},
    ]
    await msg.respond(json.dumps(messages).encode())
