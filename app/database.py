import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "ms_messaging")
DB_USERNAME = os.getenv("DB_USERNAME", "nahumfg")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nahumfg")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Crear el motor asíncrono
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

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
