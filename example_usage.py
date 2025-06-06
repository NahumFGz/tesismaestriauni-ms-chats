#!/usr/bin/env python3
"""
Ejemplo de uso del módulo llm.py refactorizado

Este archivo demuestra cómo usar las nuevas funciones simplificadas
para procesar consultas de chat sin necesidad de FastAPI.
"""

import asyncio

from app.llm import process_chat_query, shutdown_chat_processor


async def main():
    """Ejemplo de uso del procesador de chat."""

    print("🚀 Iniciando ejemplo del procesador de chat...")

    try:
        # Ejemplo 1: Consulta simple
        print("\n1. Consulta simple:")
        result1 = await process_chat_query("¿Qué puedes hacer?")
        print(f"Respuesta: {result1['response']}")
        print(f"Thread ID: {result1['thread_id']}")

        # Ejemplo 2: Consulta con contexto (mismo thread)
        print("\n2. Consulta con contexto (mismo hilo):")
        thread_id = result1["thread_id"]
        result2 = await process_chat_query("¿Puedes ser más específico?", thread_id)
        print(f"Respuesta: {result2['response']}")
        print(f"Thread ID: {result2['thread_id']}")

        # Ejemplo 3: Nueva conversación (nuevo thread)
        print("\n3. Nueva conversación:")
        result3 = await process_chat_query("Hola, soy un usuario nuevo")
        print(f"Respuesta: {result3['response']}")
        print(f"Thread ID: {result3['thread_id']}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Importante: cerrar el procesador al finalizar
        print("\n🚪 Cerrando procesador...")
        await shutdown_chat_processor()
        print("✅ Ejemplo completado")


if __name__ == "__main__":
    asyncio.run(main())
