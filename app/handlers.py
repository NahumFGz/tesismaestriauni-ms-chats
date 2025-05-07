"""
Manejadores de Mensajes NATS

Este módulo contiene los handlers que procesan los mensajes entrantes de NATS.
Cada handler:

1. handle_message_generate:
   - Topic: message.generate
   - Función: Genera una respuesta para un mensaje
   - Payload esperado: {"data": {"chat_uuid": "", "content": ""}}
   - Respuesta: {"chat_uuid": "", "content": ""}

2. handle_message_generate_streaming:
   - Topic: message.generate.streaming
   - Función: Genera una respuesta token por token
   - Payload esperado: {"data": {"chat_uuid": "", "content": ""}}
   - Respuesta: {"chat_uuid": "", "token": "", "is_complete": bool}

3. handle_chats_by_user:
   - Topic: chats.by.user
   - Función: Obtiene todos los chats de un usuario
   - Payload esperado: {"data": {"user_id": int, "take": int, "skip": int}}
   - Respuesta: Lista de chats con chat_uuid y updated_at

4. handle_messages_by_chat:
   - Topic: messages.by.chat
   - Función: Obtiene todos los mensajes de un chat específico
   - Payload esperado: {"data": {"user_id": int, "chat_uuid": str}}
   - Respuesta: Lista de mensajes ordenados por timestamp
"""

import json
import uuid
from datetime import datetime

from nats.aio.msg import Msg
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app import models
from app.chat_generator import generate_chat_response, generate_chat_tokens
from app.database import get_async_db


async def handle_message_generate(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [generate] Recibido: {payload}")

        data = payload["data"]
        content = data["content"]
        chat_uuid = data.get("chat_uuid")

        # TODO: Obtener user_id desde JWT
        user_id = 1

        if not chat_uuid:
            chat_uuid = str(uuid.uuid4())

        # Obtener la sesión de la base de datos
        async for session in get_async_db():
            # Buscar o crear el chat
            chat_query = await session.execute(
                select(models.Chat).where(models.Chat.chat_uuid == chat_uuid)
            )
            chat = chat_query.scalar_one_or_none()

            if not chat:
                chat = models.Chat(chat_uuid=chat_uuid, user_id=user_id)
                session.add(chat)
                await session.commit()
                await session.refresh(chat)

            # Guardar mensaje del usuario
            user_message = models.Message(
                content=content, chat_uuid=chat_uuid, sender_type=models.SenderType.USER
            )
            session.add(user_message)
            await session.commit()
            await session.refresh(user_message)

            # Generar respuesta del chat
            chat_response = await generate_chat_response(chat_uuid, content)

            # Guardar respuesta del chat
            bot_message = models.Message(
                content=chat_response["message"],
                chat_uuid=chat_uuid,
                sender_type=models.SenderType.SYSTEM,
            )
            session.add(bot_message)

            # Actualizar updated_at del chat
            chat.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(bot_message)

            response = {"chat_uuid": chat_uuid, "content": chat_response["message"]}
            await msg.respond(json.dumps(response).encode())
            break
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())


async def handle_message_generate_streaming(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [generate.streaming] Recibido: {payload}")

        data = payload["data"]
        content = data["content"]
        chat_uuid = data.get("chat_uuid")

        # TODO: Obtener user_id desde JWT
        user_id = 1

        if not chat_uuid:
            chat_uuid = str(uuid.uuid4())

        # Obtener la sesión de la base de datos
        async for session in get_async_db():
            # Buscar o crear el chat
            chat_query = await session.execute(
                select(models.Chat).where(models.Chat.chat_uuid == chat_uuid)
            )
            chat = chat_query.scalar_one_or_none()

            if not chat:
                chat = models.Chat(chat_uuid=chat_uuid, user_id=user_id)
                session.add(chat)
                await session.commit()
                await session.refresh(chat)

            # Guardar mensaje del usuario
            user_message = models.Message(
                content=content, chat_uuid=chat_uuid, sender_type=models.SenderType.USER
            )
            session.add(user_message)
            await session.commit()
            await session.refresh(user_message)

            # Generar respuesta token por token
            async for token_data in generate_chat_tokens(chat_uuid, content):
                response = {
                    "chat_uuid": chat_uuid,
                    "token": token_data["token"],
                    "is_complete": token_data["is_complete"],
                }
                await msg.respond(json.dumps(response).encode())

                if token_data["is_complete"]:
                    # Guardar respuesta completa del chat
                    bot_message = models.Message(
                        content=token_data["full_message"],
                        chat_uuid=chat_uuid,
                        sender_type=models.SenderType.SYSTEM,
                    )
                    session.add(bot_message)

                    # Actualizar updated_at del chat
                    chat.updated_at = datetime.utcnow()

                    await session.commit()
            break
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())


async def handle_chats_by_user(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [chats.by.user] Recibido: {payload}")

        data = payload["data"]
        user_id = data.get("user_id", 1)  # TODO: Obtener desde JWT
        take = data.get("take", 20)
        skip = data.get("skip", 0)

        async for session in get_async_db():
            query = (
                select(models.Chat)
                .where(models.Chat.user_id == user_id)
                .order_by(desc(models.Chat.updated_at), desc(models.Chat.created_at))
                .offset(skip)
                .limit(take)
            )
            result = await session.execute(query)
            chats = result.scalars().all()

            response = [
                {
                    "chat_uuid": chat.chat_uuid,
                    "updated_at": (
                        chat.updated_at.isoformat()
                        if chat.updated_at
                        else chat.created_at.isoformat()
                    ),
                }
                for chat in chats
            ]
            await msg.respond(json.dumps(response).encode())
            break
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())


async def handle_messages_by_chat(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [messages.by.chat] Recibido: {payload}")

        data = payload["data"]
        user_id = data.get("user_id", 1)  # TODO: Obtener desde JWT
        chat_uuid = data["chat_uuid"]

        # TODO: Validar que el usuario solo acceda a sus propios chats

        async for session in get_async_db():
            query = (
                select(models.Message)
                .where(models.Message.chat_uuid == chat_uuid)
                .order_by(models.Message.timestamp)
            )
            result = await session.execute(query)
            messages = result.scalars().all()

            response = [
                {"id": msg.id, "sender_type": msg.sender_type.value, "content": msg.content}
                for msg in messages
            ]
            await msg.respond(json.dumps(response).encode())
            break
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        await msg.respond(json.dumps(error_response).encode())
