"""
Este módulo contiene la función para generar títulos para los chats
utilizando un modelo de lenguaje pequeño.
"""

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

# Configuración del modelo para resumir/generar títulos
llm_title_model = init_chat_model("openai:gpt-4o-mini", temperature=0.0)


async def generate_chat_title(user_message: str) -> str:
    """
    Genera un título breve para un chat basado en el primer mensaje del usuario.

    Args:
        user_message: El mensaje del usuario

    Returns:
        str: Un título corto para el chat
    """
    system_prompt = "Eres un asistente que genera un título descriptivo y conciso para una conversación basado en el primer mensaje. El título debe tener máximo 7 palabras."
    system_message = SystemMessage(content=system_prompt)
    human_message = HumanMessage(content=user_message)

    response = await llm_title_model.ainvoke([system_message, human_message])
    # Limpiamos cualquier comilla o carácter especial que pueda venir en el título
    title = response.content.strip().strip("\"'")
    return title
