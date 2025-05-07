"""
Simulación de generación de respuestas de chat.

Este módulo contiene dos funciones asíncronas que simulan el comportamiento de un sistema de generación de respuestas tipo chatbot:

1. `generate_chat_response`: simula la generación de una respuesta completa en un solo paso.
2. `generate_chat_tokens`: simula una respuesta generada token por token (palabra por palabra), útil para pruebas de emisión en tiempo real (streaming).

Estas funciones son útiles para pruebas de integración con WebSockets, NATS, SSE u otras arquitecturas reactivas, antes de integrar un modelo de lenguaje real.
"""

import asyncio
from typing import Any, AsyncGenerator


async def generate_chat_response(chat_uuid: str, message: str) -> dict:
    # Lista de posibles respuestas
    responses = [
        "¡Hola! Gracias por tu mensaje. Me parece muy interesante lo que comentas. ¿Podrías darme más detalles al respecto?",
        "Entiendo tu punto de vista. Basándome en la información disponible, te sugiero considerar las siguientes alternativas...",
        "Es un tema fascinante. Desde mi perspectiva, hay varios aspectos importantes que podríamos analizar con más profundidad.",
        "Gracias por compartir eso conmigo. Me gustaría explorar más este tema contigo y entender mejor tu perspectiva.",
        "Interesante planteamiento. Permíteme ofrecerte una perspectiva diferente que podría ser útil para esta situación.",
    ]

    # Simula tiempo de procesamiento
    await asyncio.sleep(0.1)

    # Selecciona una respuesta aleatoria
    import random

    response = random.choice(responses)

    return {"chat_uuid": chat_uuid, "message": response}


async def generate_chat_tokens(chat_uuid: str, message: str) -> AsyncGenerator[dict, Any]:
    response = message + " desde el chat_response"
    tokens = response.split()  # Simula tokens dividiendo por espacios

    for token in tokens:
        await asyncio.sleep(0.1)  # Simula delay entre tokens
        yield {"chat_uuid": chat_uuid, "token": token, "is_complete": False}

    # Señal de finalización del stream
    yield {"chat_uuid": chat_uuid, "token": "", "is_complete": True}
