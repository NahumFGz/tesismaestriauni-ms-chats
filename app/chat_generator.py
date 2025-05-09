"""
Simulación de generación de respuestas de chat.

Este módulo contiene funciones para interactuar con el servicio de chat a través de una API HTTP.
"""

import asyncio
from typing import Any, AsyncGenerator

import aiohttp


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    """
    Genera una respuesta de chat haciendo una llamada a la API local.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Returns:
        dict: Respuesta del servicio de chat
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/query", json={"query": message, "thread_id": chat_uuid}
        ) as response:
            result = await response.json()
            return {
                "chat_uuid": chat_uuid,
                "message": result.get("result", {}).get(
                    "response", "Lo siento, no pude procesar tu mensaje."
                ),
            }


async def generate_chat_tokens(chat_uuid: str, message: str) -> AsyncGenerator[dict, Any]:
    response = message + " desde el chat_response"
    tokens = response.split()  # Simula tokens dividiendo por espacios
    full_message = ""

    for token in tokens:
        await asyncio.sleep(0.1)  # Simula delay entre tokens
        full_message += token + " "
        yield {
            "chat_uuid": chat_uuid,
            "token": token,
            "is_complete": False,
            "full_message": full_message.strip(),
        }

    # Señal de finalización del stream
    yield {
        "chat_uuid": chat_uuid,
        "token": "",
        "is_complete": True,
        "full_message": full_message.strip(),
    }
