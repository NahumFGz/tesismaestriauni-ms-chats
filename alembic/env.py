"""
env.py - Archivo de configuración de migraciones para Alembic (usando SQLAlchemy Async)

Este archivo es generado y utilizado por Alembic para gestionar migraciones de bases de datos.
Define cómo se conecta Alembic a la base de datos (ya sea en modo online o offline) y cómo detecta
cambios en los modelos para autogenerar scripts de migración. En este caso, está adaptado para trabajar
con SQLAlchemy en modo asíncrono.

Se encarga de:
1. Configurar la conexión a la base de datos.
2. Definir la metadata de los modelos para autogeneración.
3. Ejecutar las migraciones en modo síncrono (offline) o asíncrono (online).
"""

import asyncio
from logging.config import fileConfig

# Importa configuración de conexión y herramientas de SQLAlchemy
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

# Herramientas propias de Alembic
from alembic import context

# Configuraciones y modelos de la aplicación
from app.config import settings
from app.database import Base
from app.model import (
    Message,  # Importación necesaria para que Alembic detecte el modelo
)

# Objeto de configuración de Alembic
config = context.config

# Configura el logging si hay archivo de configuración
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de los modelos de SQLAlchemy que Alembic usará para autogenerar migraciones
target_metadata = Base.metadata


# Función que aplica las migraciones usando una conexión activa
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


# Función para ejecutar migraciones en modo online (requiere conexión a BD)
async def run_async_migrations() -> None:
    # Recupera configuración desde el archivo alembic.ini y actualiza la URL de la BD
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    # Crea un motor asíncrono para conectarse a la base de datos
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    # Ejecuta las migraciones con la conexión establecida
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# Función para ejecutar migraciones en modo offline (sin conexión activa)
def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Función principal que determina si correr online
def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# Ejecuta la migración dependiendo del modo (offline/online)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
