import json
from datetime import datetime

from nats.aio.msg import Msg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
