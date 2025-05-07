"""
Configuración de la Base de Datos Asíncrona

Este módulo configura la conexión asíncrona a PostgreSQL usando SQLAlchemy.
Proporciona:

1. Configuración de la Conexión:
   - Usa la configuración centralizada de config.py
   - Motor asíncrono de SQLAlchemy

2. Gestión de Sesiones:
   - Fábrica de sesiones asíncronas
   - Función get_db para inyección de dependencias
   - Manejo automático de cierre de sesiones

3. Modelo Base:
   - Clase base para todos los modelos SQLAlchemy

Notas:
- Usa asyncpg como driver asíncrono
- Implementa patrones de conexión seguros
- Maneja el ciclo de vida de las sesiones
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# Crear el motor asíncrono usando la URL de la configuración
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Crear la fábrica de sesiones asíncronas
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# Función para obtener una sesión de base de datos
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
