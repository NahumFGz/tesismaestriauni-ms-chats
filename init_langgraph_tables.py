"""
Este script inicializa las tablas necesarias para guardar la memoria del grafo
LangGraph en una base de datos PostgreSQL usando el módulo AsyncPostgresSaver.

Debe ejecutarse una única vez antes de usar LangGraph con memoria persistente,
ya que crea las tablas requeridas como `checkpoints`, `checkpoint_writes`, etc.

Uso:
    python init_langgraph_tables.py
"""

import asyncio

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import get_settings

settings = get_settings()


async def main():
    print("🚀 Iniciando setup de memoria persistente para LangGraph...")

    # Crear un pool de conexiones asíncronas hacia PostgreSQL
    pool = AsyncConnectionPool(
        conninfo=settings.database_memory_url,
        min_size=1,  # mínimo 1 conexión en el pool
        max_size=1,  # máximo 1 conexión (suficiente para setup inicial)
        open=False,  # no abrir automáticamente al crear, se abrirá manualmente abajo
        kwargs={
            "autocommit": True,  # ejecutar automáticamente cada sentencia (evita `BEGIN`)
            "row_factory": dict_row,  # resultados como diccionarios en vez de tuplas
            "prepare_threshold": 0,  # desactiva el caché de consultas preparadas (previene errores con algunas herramientas)
        },
    )

    # Abrir la conexión al pool (asíncronamente)
    await pool.open()
    print("✅ Conexión a PostgreSQL establecida.")

    # Crear el objeto que guarda memoria de LangGraph usando PostgreSQL
    saver = AsyncPostgresSaver(pool)

    print("🛠️  Ejecutando `setup()` para crear/migrar tablas necesarias...")
    await saver.setup()  # crea las tablas si no existen; es idempotente (puede llamarse múltiples veces sin efectos negativos)
    print("✅ Tablas de memoria para LangGraph listas.")

    # Cerrar la conexión limpia y explícitamente
    await pool.close()
    print("👋 Conexión cerrada correctamente.")


# Ejecutar el script si se invoca directamente
if __name__ == "__main__":
    asyncio.run(main())
