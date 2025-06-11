"""
Este módulo contiene funciones para interactuar con el procesador de chat MCP.
"""

import asyncio
from typing import Any, AsyncGenerator

# Importamos las funciones del módulo agent LLM
from app.agent.llm import run, run_stream


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    """
    Genera una respuesta de chat usando el procesador MCP.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Returns:
        dict: Respuesta del servicio de chat
    """
    result = await run(message, chat_uuid)

    return {
        "chat_uuid": chat_uuid,
        "message": result.get("response", "Lo siento, no pude procesar tu mensaje."),
    }


async def generate_chat_tokens(chat_uuid: str, message: str) -> AsyncGenerator[dict, Any]:
    """
    Genera tokens de chat usando streaming real del procesador MCP.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Yields:
        dict: Información de cada token y el mensaje completo
    """
    async for chunk in run_stream(message, chat_uuid):
        # Si el chunk indica que el streaming está completo
        if chunk.get("is_complete", False):
            yield {
                "chat_uuid": chat_uuid,
                "token": "",
                "is_complete": True,
                "full_message": chunk.get("full_message", ""),
            }

        else:
            # Streaming de tokens individuales
            yield {
                "chat_uuid": chat_uuid,
                "token": chunk.get("token", ""),
                "is_complete": False,
                "full_message": chunk.get("full_message", ""),
            }
