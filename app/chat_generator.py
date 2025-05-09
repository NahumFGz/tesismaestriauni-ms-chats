"""
Este módulo contiene funciones para interactuar directamente con el procesador MCP.
TODO: Implementar el streaming de tokens, pero será con otro procesador MCP.
"""

import asyncio
from typing import Any, AsyncGenerator

# Importamos el procesador MCP directamente
from app.llm import MCPQueryProcessor

# Instancia global del procesador
_processor = None


async def get_processor() -> MCPQueryProcessor:
    """
    Obtiene o inicializa el procesador MCP.

    Returns:
        MCPQueryProcessor: Instancia del procesador MCP
    """
    global _processor
    if _processor is None:
        _processor = MCPQueryProcessor()
        await _processor.start()
    return _processor


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    """
    Genera una respuesta de chat usando directamente el procesador MCP.

    Args:
        chat_uuid: El ID del hilo de chat
        message: El mensaje del usuario

    Returns:
        dict: Respuesta del servicio de chat
    """
    processor = await get_processor()
    result = await processor.run(message, chat_uuid)

    return {
        "chat_uuid": chat_uuid,
        "message": result.get("response", "Lo siento, no pude procesar tu mensaje."),
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
