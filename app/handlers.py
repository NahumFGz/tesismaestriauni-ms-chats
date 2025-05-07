"""
Manejadores de Mensajes NATS

Este módulo contiene los handlers que procesan los mensajes entrantes de NATS.
Cada handler:

1. Recibe mensajes de un topic específico
2. Procesa la información
3. Interactúa con la base de datos
4. Envía una respuesta

Handlers Implementados:

1. handle_create:
   - Topic: message.create
   - Función: Crea un nuevo mensaje en la base de datos
   - Payload esperado: {"data": {"content": "texto del mensaje"}}
   - Respuesta: Mensaje creado con ID y timestamps

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

from nats.aio.msg import Msg
from sqlalchemy import select

from app import database, model


async def handle_create(msg: Msg):
    try:
        payload = json.loads(msg.data.decode())
        print(f"📨 [create] Recibido: {payload}")

        content = payload["data"]["content"]

        # Obtener la sesión de la base de datos
        session = database.async_session()
        try:
            db_message = model.Message(content=content)
            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)

            response = {
                "status": "ok",
                "data": {
                    "id": db_message.id,
                    "content": db_message.content,
                    "created_at": db_message.created_at.isoformat(),
                    "updated_at": (
                        db_message.updated_at.isoformat() if db_message.updated_at else None
                    ),
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
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "updated_at": msg.updated_at.isoformat() if msg.updated_at else None,
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
