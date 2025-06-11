from typing import List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage


def format_history_context(
    messages: List, max_chars: int = 200, exclude_last: bool = True, last_n: int = 5
) -> str:
    """
    Formatea el historial en pares Q: A: excluyendo la última pregunta.
    - Agrupa en pares (HumanMessage, AIMessage).
    - Muestra pregunta completa con prefijo Q:.
    - Trunca cada respuesta a max_chars con prefijo A: y añade '…'.
    - Cada par en una línea separada.
    - Solo incluye los últimos last_n pares.
    """
    pairs: List[Tuple[HumanMessage, Optional[AIMessage]]] = []
    pending_human = None

    # Si exclude_last=True, no procesamos el último mensaje
    messages_to_process = messages[:-1] if exclude_last and messages else messages

    for msg in messages_to_process:
        if isinstance(msg, HumanMessage):
            # Si ya había un HumanMessage pendiente, lo guardamos sin respuesta
            if pending_human is not None:
                pairs.append((pending_human, None))
            pending_human = msg
        elif isinstance(msg, AIMessage) and pending_human is not None:
            pairs.append((pending_human, msg))
            pending_human = None

    # Guardar el último HumanMessage si quedó pendiente
    if pending_human is not None:
        pairs.append((pending_human, None))

    # Tomar solo los últimos last_n pares
    recent_pairs = pairs[-last_n:] if last_n > 0 else pairs

    lines = []
    for human, ai in recent_pairs:
        # Pregunta completa con prefijo Q:
        q = human.content.strip()
        lines.append(f"Q: {q}")

        # Respuesta truncada con prefijo A: (si existe)
        if ai is not None:
            # Manejar tanto contenido string como lista (tool calls)
            if isinstance(ai.content, str):
                a = ai.content.strip()
            elif isinstance(ai.content, list):
                # Extraer solo el texto de la lista, ignorando tool_use
                text_parts = []
                for item in ai.content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                a = " ".join(text_parts).strip()
            else:
                a = str(ai.content).strip()

            if len(a) > max_chars:
                # Buscar el último espacio antes del límite para no cortar palabras
                cut_point = a.rfind(" ", 0, max_chars)
                if cut_point == -1:
                    cut_point = max_chars
                snippet = a[:cut_point].rstrip() + "…"
            else:
                snippet = a
            lines.append(f"A: {snippet}")
        else:
            # Si no hay respuesta, indicamos que no hay respuesta
            lines.append("A: [Pendiente de responder...]")

        # Línea vacía entre pares para separar
        lines.append("")

    return "\n".join(lines).strip()


def get_last_question(messages: List) -> str:
    """
    Obtiene la última pregunta del usuario de la lista de mensajes.
    """
    if not messages:
        return ""

    # Buscar el último HumanMessage
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            # Manejar tanto contenido string como lista
            if isinstance(msg.content, str):
                return msg.content.strip()
            elif isinstance(msg.content, list):
                # Extraer solo el texto de la lista
                text_parts = []
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                return " ".join(text_parts).strip()
            else:
                return str(msg.content).strip()

    return ""
