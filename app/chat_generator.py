import asyncio


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    await asyncio.sleep(0.01)
    return {"chat_uuid": chat_uuid, "message": message + "desde el chat_response"}
