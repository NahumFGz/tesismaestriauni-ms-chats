"""
Este módulo contiene funciones para interactuar con el procesador de chat MCP.
TODO: Implementar el streaming de tokens, pero será con otro procesador MCP.
"""

import asyncio
from typing import Any, AsyncGenerator

# Importamos las funciones simplificadas del módulo LLM
from app.llm import process_chat_query


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    """
    Genera una respuesta de chat usando el procesador MCP.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Returns:
        dict: Respuesta del servicio de chat
    """
    result = await process_chat_query(message, chat_uuid)

    return {
        "chat_uuid": chat_uuid,
        "message": result.get("response", "Lo siento, no pude procesar tu mensaje."),
    }


async def generate_chat_tokens(chat_uuid: str, message: str) -> AsyncGenerator[dict, Any]:
    """
    Genera tokens de chat de forma simulada (streaming).
    TODO: Implementar streaming real con el procesador MCP.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Yields:
        dict: Información de cada token y el mensaje completo
    """
    # Por ahora, simulamos el streaming dividiendo la respuesta
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
