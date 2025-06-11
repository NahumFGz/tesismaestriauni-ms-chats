"""
handlers.py
===========

Manejadores de mensajes para el microservicio **ms‑messages**.

Flujo general
-------------
1. **message.generate**                  →   El gateway publica un payload con
                                            `{"data": {"chat_uuid"?, "content"}}`.
   •  Guardamos el mensaje del usuario en la BD.
   •  Pedimos una respuesta completa a `generate_chat_response`.
   •  Persistimos la respuesta del sistema y devolvemos un *reply* con
      `{"chat_uuid", "content"}`.

2. **message.generate.streaming.start**  →   El gateway publica un payload con
                                            `{"stream_subject", "chat_uuid"?, "content"}`.
   •  Guardamos el mensaje del usuario igual que arriba.
   •  Recibimos tokens de `generate_chat_tokens` y los publicamos en
      `stream_subject`.
   •  Al terminar, persistimos la respuesta completa y marcamos
      `is_complete=True`.

3. **chats.by.user**                     →   Reply con los chats más recientes
                                            del usuario.
4. **messages.by.chat**                  →   Reply con los mensajes de un chat.

Notas
-----
*  El `user_id` está hard‑codeado en **1** por ahora (→ TODO: extraerlo del JWT).
*  Se eliminaron duplicaciones con pequeñas funciones auxiliares:
   `_get_or_create_chat`, `_save_user_message`, `_save_bot_message`,
   `_reply_error`.
"""

import json
import uuid
from datetime import datetime

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from sqlalchemy import desc, select

from app import models
from app.chat_generator import generate_chat_response, generate_chat_tokens
from app.database import get_async_db
from app.llm_resumer import generate_chat_title

# --------------------------------------------------------------------------- #
# Helpers (DRY)                                                               #
# --------------------------------------------------------------------------- #


async def _get_or_create_chat(session, chat_uuid: str, user_id: int) -> models.Chat:
    """Devuelve el chat existente o lo crea si no existe."""
    chat = (
        (await session.execute(select(models.Chat).where(models.Chat.chat_uuid == chat_uuid)))
        .scalars()
        .first()
    )
    if chat is None:
        chat = models.Chat(chat_uuid=chat_uuid, user_id=user_id)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
    return chat


async def _save_user_message(session, chat_uuid: str, content: str) -> None:
    """Guarda el mensaje enviado por el usuario."""
    session.add(
        models.Message(
            content=content,
            chat_uuid=chat_uuid,
            sender_type=models.SenderType.USER,
        )
    )
    await session.commit()


async def _save_bot_message(session, chat: models.Chat, content: str) -> None:
    """Guarda la respuesta del sistema y actualiza la marca de tiempo del chat."""
    session.add(
        models.Message(
            content=content,
            chat_uuid=chat.chat_uuid,
            sender_type=models.SenderType.SYSTEM,
        )
    )
    chat.updated_at = datetime.utcnow()
    await session.commit()


async def _reply_error(msg: Msg, exc: Exception) -> None:
    """Envía un reply de error estandarizado."""
    await msg.respond(json.dumps({"status": "error", "message": str(exc)}).encode())


async def _generate_and_save_title_if_needed(
    session, chat: models.Chat, content: str, is_new_chat: bool
) -> str:
    """
    Genera y guarda un título para el chat si es necesario.
    Si falla la generación, usa "Chat #[ID]" como título.
    Devuelve el título generado o None.
    """
    generated_title = None
    if is_new_chat and not chat.title:
        try:
            generated_title = await generate_chat_title(content)
        except Exception:  # pragma: no cover
            # Si falla la generación del título, usamos un título por defecto
            generated_title = f"Chat #{chat.id}"

        chat.title = generated_title
        await session.commit()
    return generated_title


# --------------------------------------------------------------------------- #
# 1. Generación de mensaje completo                                           #
# --------------------------------------------------------------------------- #
async def handle_message_generate(msg: Msg) -> None:
    """Procesa `message.generate`, genera título para nuevos chats y devuelve la respuesta completa en el reply."""
    try:
        payload = json.loads(msg.data.decode())
        data = payload["data"]

        content: str = data["content"]
        chat_uuid: str = data.get("chat_uuid") or str(uuid.uuid4())
        user_id = 1  # TODO: extraer del JWT

        is_new_chat = (
            "chat_uuid" not in data or data["chat_uuid"] is None or data["chat_uuid"] == ""
        )

        async for session in get_async_db():
            chat = await _get_or_create_chat(session, chat_uuid, user_id)
            await _save_user_message(session, chat_uuid, content)

            # Si es un nuevo chat, generamos título
            generated_title = await _generate_and_save_title_if_needed(
                session, chat, content, is_new_chat
            )

            chat_resp = await generate_chat_response(chat_uuid, content)
            await _save_bot_message(session, chat, chat_resp["message"])

            # Incluimos el título en la respuesta si se generó uno nuevo
            response_data = {"chat_uuid": chat_uuid, "content": chat_resp["message"]}

            if generated_title:
                response_data["title"] = generated_title

            await msg.respond(json.dumps(response_data).encode())
            break
    except Exception as exc:  # pragma: no cover
        await _reply_error(msg, exc)


# --------------------------------------------------------------------------- #
# 2. Generación de mensaje token‑a‑token (streaming)                          #
# --------------------------------------------------------------------------- #
async def handle_message_generate_stream_start(nc: NATS, msg: Msg) -> None:
    """
    Procesa `message.generate.streaming.start`.

    Publica cada token en `stream_subject`. Cuando `is_complete=True`, guarda
    la respuesta completa en la BD.
    """
    try:
        payload = json.loads(msg.data.decode())
        stream_subject: str = payload["stream_subject"]

        chat_uuid: str = payload.get("chat_uuid") or str(uuid.uuid4())
        content: str = payload["content"]
        user_id = 1  # TODO: extraer del JWT

        is_new_chat = (
            "chat_uuid" not in payload or payload["chat_uuid"] is None or payload["chat_uuid"] == ""
        )
        generated_title = None
        full_message = ""

        async for session in get_async_db():
            chat = await _get_or_create_chat(session, chat_uuid, user_id)
            await _save_user_message(session, chat_uuid, content)

            # Si es un nuevo chat, generamos título
            generated_title = await _generate_and_save_title_if_needed(
                session, chat, content, is_new_chat
            )

            async for token_data in generate_chat_tokens(chat_uuid, content):
                token: str = token_data["token"]
                is_complete: bool = token_data["is_complete"]

                if token:
                    full_message += token

                response_data = {
                    "chat_uuid": chat_uuid,
                    "token": token,
                    "is_complete": is_complete,
                    "full_message": full_message,
                }

                # Solo incluimos el título en el último mensaje cuando is_complete=True
                if is_complete and generated_title:
                    response_data["title"] = generated_title

                await nc.publish(
                    stream_subject,
                    json.dumps(response_data).encode(),
                )

                if is_complete:
                    await _save_bot_message(session, chat, full_message)
            break

    except Exception as exc:  # pragma: no cover
        await nc.publish(
            payload.get("stream_subject", ""),
            json.dumps({"status": "error", "message": str(exc)}).encode(),
        )


# --------------------------------------------------------------------------- #
# 3. Consulta de chats por usuario                                            #
# --------------------------------------------------------------------------- #
async def handle_chats_by_user(msg: Msg) -> None:
    """Procesa `chats.by.user` y devuelve los chats más recientes del usuario (paginado por page y take)."""
    try:
        payload = json.loads(msg.data.decode())
        data = payload["data"]

        user_id = data.get("user_id", 1)  # TODO: JWT
        take = data.get("take", 20)
        page = max(data.get("page", 1), 1)
        skip = (page - 1) * take

        async for session in get_async_db():
            query = (
                select(models.Chat)
                .where(models.Chat.user_id == user_id)
                .order_by(desc(models.Chat.updated_at), desc(models.Chat.created_at))
                .offset(skip)
                .limit(take)
            )
            chats = (await session.execute(query)).scalars().all()

            response = [
                {
                    "id": c.id,
                    "title": c.title,
                    "chat_uuid": c.chat_uuid,
                    "updated_at": (
                        c.updated_at.isoformat() if c.updated_at else c.created_at.isoformat()
                    ),
                }
                for c in chats
            ]
            await msg.respond(json.dumps(response).encode())
            break
    except Exception as exc:  # pragma: no cover
        await _reply_error(msg, exc)


# --------------------------------------------------------------------------- #
# 4. Consulta de mensajes por chat                                            #
# --------------------------------------------------------------------------- #
async def handle_messages_by_chat(msg: Msg) -> None:
    """Procesa `messages.by.chat` y devuelve los mensajes de un chat."""
    try:
        payload = json.loads(msg.data.decode())
        data = payload["data"]

        user_id = data.get("user_id", 1)  # TODO: JWT
        chat_uuid: str = data["chat_uuid"]

        # TODO: validar que *chat_uuid* pertenezca a *user_id*

        async for session in get_async_db():
            query = (
                select(models.Message)
                .where(models.Message.chat_uuid == chat_uuid)
                .order_by(models.Message.timestamp)
            )
            messages = (await session.execute(query)).scalars().all()

            response = [
                {
                    "id": m.id,
                    "sender_type": m.sender_type.value,
                    "content": m.content,
                }
                for m in messages
            ]
            await msg.respond(json.dumps(response).encode())
            break
    except Exception as exc:  # pragma: no cover
        await _reply_error(msg, exc)
