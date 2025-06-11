"""
Módulo de inicialización centralizada de servicios.

Responsabilidades:
- Inicializar conexión a PostgreSQL y AsyncPostgresSaver
- Inicializar herramientas de transparencia (locales + remotas)
- Gestionar variables globales de la aplicación
- Proporcionar funciones de limpieza de recursos
"""

from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.agent.tools_local import tools_local_list
from app.agent.tools_remote import get_remote_tools, shutdown_mcp_connections
from app.config import get_settings

settings = get_settings()

# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

# Variables globales para el pool de conexiones y memory saver
_connection_pool: Optional[AsyncConnectionPool] = None
_memory_saver: Optional[AsyncPostgresSaver] = None

# Variables globales para herramientas
_transparency_tools = []
_remote_tools_initialized = False

# ============================================================================
# INICIALIZADORES
# ============================================================================


async def initialize_database_memory() -> AsyncPostgresSaver:
    """
    Inicializa el pool de conexiones PostgreSQL y el AsyncPostgresSaver.

    Returns:
        AsyncPostgresSaver: Instancia del memory saver inicializada

    Raises:
        Exception: Si hay error en la inicialización de PostgreSQL
    """
    global _connection_pool, _memory_saver

    if _memory_saver is not None:
        return _memory_saver

    try:
        # Crear el pool de conexiones sin abrirlo en el constructor
        _connection_pool = AsyncConnectionPool(
            conninfo=settings.database_memory_url,
            max_size=20,  # 🚀 Más conexiones para alta concurrencia
            min_size=5,  # 🎯 Mantener conexiones mínimas activas
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,  # evita errores con statements cacheados
            },
            open=False,  # Importante: no abrir en el constructor
        )

        # Abrir el pool explícitamente
        await _connection_pool.open()

        # Crear el AsyncPostgresSaver con el pool
        _memory_saver = AsyncPostgresSaver(_connection_pool)

        print("✅ Base de datos PostgreSQL inicializada correctamente")

    except Exception as e:
        print(f"⚠️  Error al inicializar PostgreSQL: {e}")
        raise

    return _memory_saver


async def initialize_transparency_tools() -> list:
    """
    Inicializa y combina las herramientas locales con las remotas de MCP.

    Returns:
        list: Lista combinada de herramientas locales y remotas
    """
    global _transparency_tools, _remote_tools_initialized

    if _remote_tools_initialized:
        return _transparency_tools

    try:
        # Obtener herramientas remotas
        remote_tools = await get_remote_tools()

        # Combinar herramientas locales y remotas
        _transparency_tools = tools_local_list + remote_tools
        _remote_tools_initialized = True

        print(
            f"✅ Herramientas de transparencia inicializadas: "
            f"{len(tools_local_list)} locales + {len(remote_tools)} remotas = "
            f"{len(_transparency_tools)} total"
        )

    except Exception as e:
        print(f"⚠️  Error al inicializar herramientas remotas: {e}")
        print("🔄 Continuando solo con herramientas locales...")
        _transparency_tools = tools_local_list
        _remote_tools_initialized = True

    return _transparency_tools


async def initialize_all_services():
    """
    Inicializa todos los servicios de la aplicación.

    Returns:
        tuple: (memory_saver, transparency_tools)
    """
    print("🚀 Iniciando inicialización de servicios...")

    # Inicializar servicios en paralelo
    import asyncio

    memory_task = asyncio.create_task(initialize_database_memory())
    tools_task = asyncio.create_task(initialize_transparency_tools())

    memory_saver = await memory_task
    transparency_tools = await tools_task

    print("✅ Todos los servicios inicializados correctamente")

    return memory_saver, transparency_tools


# ============================================================================
# GETTERS PARA SERVICIOS INICIALIZADOS
# ============================================================================


def get_memory_saver() -> Optional[AsyncPostgresSaver]:
    """
    Obtiene el AsyncPostgresSaver inicializado.

    Returns:
        AsyncPostgresSaver: Memory saver si está inicializado, None en caso contrario
    """
    return _memory_saver


def get_transparency_tools() -> list:
    """
    Obtiene las herramientas de transparencia inicializadas.

    Returns:
        list: Lista de herramientas de transparencia
    """
    return _transparency_tools


def is_database_initialized() -> bool:
    """
    Verifica si la base de datos está inicializada.

    Returns:
        bool: True si está inicializada, False en caso contrario
    """
    return _memory_saver is not None


def is_tools_initialized() -> bool:
    """
    Verifica si las herramientas están inicializadas.

    Returns:
        bool: True si están inicializadas, False en caso contrario
    """
    return _remote_tools_initialized


# ============================================================================
# LIMPIEZA DE RECURSOS
# ============================================================================


async def cleanup_initializer_resources():
    """
    Función para limpiar TODOS los recursos de la aplicación (MCP, PostgreSQL, LLM, etc.)
    Debe ser llamada al finalizar la aplicación.
    """
    global _connection_pool, _memory_saver, _transparency_tools, _remote_tools_initialized

    try:
        print("🧹 Iniciando limpieza completa de recursos...")

        # Limpiar recursos del LLM (grafo compilado)
        try:
            from app.agent.llm import cleanup_llm_resources

            await cleanup_llm_resources()
        except ImportError:
            print("⚠️  No se pudo importar cleanup_llm_resources")

        # Cerrar conexiones MCP
        await shutdown_mcp_connections()

        # Cerrar AsyncPostgresSaver si existe
        if _memory_saver is not None:
            # AsyncPostgresSaver no tiene método close explícito, pero debemos liberar la referencia
            _memory_saver = None
            print("🗄️  AsyncPostgresSaver liberado")

        # Cerrar pool de conexiones PostgreSQL
        if _connection_pool is not None:
            await _connection_pool.close()
            _connection_pool = None
            print("🗄️  Pool de conexiones PostgreSQL cerrado")

        # Resetear variables de herramientas
        _transparency_tools = []
        _remote_tools_initialized = False

        print("✅ Todos los recursos limpiados exitosamente.")

    except Exception as e:
        print(f"⚠️  Error al limpiar recursos: {e}")


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================


async def ensure_services_initialized():
    """
    Asegura que todos los servicios estén inicializados.
    Si no lo están, los inicializa.

    Returns:
        tuple: (memory_saver, transparency_tools)
    """
    if not is_database_initialized() or not is_tools_initialized():
        return await initialize_all_services()

    return get_memory_saver(), get_transparency_tools()
