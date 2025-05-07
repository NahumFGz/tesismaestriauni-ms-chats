"""
Manejadores de Mensajes NATS

Este módulo contiene los handlers que procesan los mensajes entrantes de NATS.
Cada handler:

1. handle_chat_message:
   - Topic: message.create
   - Función: Crea un nuevo mensaje en la base de datos y genera una respuesta
   - Payload esperado: {"data": {"content": "texto del mensaje", "chat_uuid": "uuid-opcional"}}
   - Respuesta: Mensaje creado con ID y timestamp, y la respuesta generada

2. handle_find_all:
   - Topic: message.findAll
   - Función: Obtiene todos los mensajes de la base de datos
   - No requiere payload
   - Respuesta: Lista de todos los mensajes

Notas:
- Manejo asíncrono de la base de datos
- Gestión de errores incluida
- Respuestas en formato JSON
"""

import json
import uuid

from nats.aio.msg import Msg
from sqlalchemy import select

from app import database, model
from app.chat_generator import generate_chat_response


async def handle_chat_message(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [create] Recibido: {payload}")

        content = payload["data"]["content"]
        # Generar UUID si no se proporciona uno o está vacío
        chat_uuid = payload["data"].get("chat_uuid")
        if not chat_uuid:
            chat_uuid = str(uuid.uuid4())

        # Obtener la sesión de la base de datos
        session = database.async_session()
        try:
            # Guardar mensaje del usuario
            user_message = model.Message(content=content, chat_uuid=chat_uuid)
            session.add(user_message)
            await session.commit()
            await session.refresh(user_message)

            # Generar respuesta del chat usando el mismo chat_uuid
            chat_response = await generate_chat_response(chat_uuid, content)

            # Guardar respuesta del chat
            bot_message = model.Message(content=chat_response["message"], chat_uuid=chat_uuid)
            session.add(bot_message)
            await session.commit()
            await session.refresh(bot_message)

            response = {
                "status": "ok",
                "data": {
                    "chat_uuid": chat_uuid,  # Incluir el chat_uuid en la respuesta
                    "user_message": {
                        "id": user_message.id,
                        "chat_uuid": user_message.chat_uuid,
                        "content": user_message.content,
                        "timestamp": user_message.timestamp.isoformat(),
                    },
                    "bot_message": {
                        "id": bot_message.id,
                        "chat_uuid": bot_message.chat_uuid,
                        "content": bot_message.content,
                        "timestamp": bot_message.timestamp.isoformat(),
                    },
                },
            }
            await msg.respond(json.dumps(response).encode())
        finally:
            await session.close()
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())


async def handle_find_all(msg: Msg):
    try:
        print("📨 [findAll] Solicitud recibida")

        # Obtener la sesión de la base de datos
        session = database.async_session()
        try:
            result = await session.execute(select(model.Message))
            messages = result.scalars().all()

            response = {
                "status": "ok",
                "data": [
                    {
                        "id": msg.id,
                        "chat_uuid": msg.chat_uuid,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in messages
                ],
            }
            await msg.respond(json.dumps(response).encode())
        finally:
            await session.close()
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())
