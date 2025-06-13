"""
Módulo para gestión de herramientas remotas MCP.

Responsabilidades:
- Gestionar conexiones a servidores MCP remotos
- Obtener herramientas disponibles de los servidores
- Manejar el ciclo de vida de las conexiones
- Proporcionar interfaz para obtener herramientas remotas
"""

from typing import Optional

from app.config import get_settings
from langchain_mcp_adapters.client import MultiServerMCPClient

settings = get_settings()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Configuración de Servidores MCP
SERVERS = {
    "attendance": {"url": settings.MCP_ATTENDANCE_URL, "transport": "streamable_http"},
    "budget": {"url": settings.MCP_BUDGET_URL, "transport": "streamable_http"},
    "voting": {"url": settings.MCP_VOTING_URL, "transport": "streamable_http"},
}


# ============================================================================
# GESTOR DE HERRAMIENTAS MCP
# ============================================================================


class MCPToolsManager:
    """
    Gestor global para las conexiones MCP y herramientas remotas.
    Mantiene las conexiones activas durante toda la aplicación.
    """

    def __init__(self):
        self._client: Optional[MultiServerMCPClient] = None
        self._tools = []
        self._is_initialized = False

    async def initialize(self) -> None:
        """Inicializa la conexión MCP y obtiene las herramientas."""
        if self._is_initialized:
            return

        print("🔄 Iniciando conexión a servidores MCP...")

        try:
            # Inicializar conexión MCP con la nueva API
            self._client = MultiServerMCPClient(SERVERS)

            # Obtener herramientas MCP (ahora es awaitable según la nueva API)
            self._tools = await self._client.get_tools()

            self._is_initialized = True

            print(f"✅ Conexión exitosa. Total de herramientas: {len(self._tools)}")

        except Exception as e:
            print(f"❌ Error al conectar con servidores MCP: {str(e)}")
            print("🔄 Usando modo fallback sin herramientas remotas")

            # Fallback sin herramientas remotas
            self._tools = []
            self._is_initialized = True

            print(f"✅ Modo fallback activo. Total de herramientas: {len(self._tools)}")

    async def shutdown(self) -> None:
        """Cierra las conexiones MCP."""
        if self._client is not None:
            try:
                # Ya no necesitamos cerrar manualmente las conexiones
                # La nueva API maneja esto automáticamente
                self._client = None
                self._tools = []
                self._is_initialized = False
                print("✅ Conexiones MCP liberadas")
            except Exception as e:
                print(f"⚠️  Error al liberar conexiones: {e}")

    def get_tools(self) -> list:
        """Obtiene la lista de herramientas disponibles."""
        if not self._is_initialized:
            raise RuntimeError("MCPToolsManager no inicializado. Llama a initialize() primero.")
        return self._tools

    @property
    def is_initialized(self) -> bool:
        """Indica si el manager ha sido inicializado."""
        return self._is_initialized


# ============================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# ============================================================================

_mcp_manager: Optional[MCPToolsManager] = None


async def get_mcp_tools_manager() -> MCPToolsManager:
    """
    Obtiene o inicializa el gestor de herramientas MCP.

    Returns:
        MCPToolsManager: Instancia del gestor MCP
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPToolsManager()
        await _mcp_manager.initialize()
    elif not _mcp_manager.is_initialized:
        await _mcp_manager.initialize()
    return _mcp_manager


async def get_remote_tools() -> list:
    """
    Función de conveniencia para obtener las herramientas remotas.

    Returns:
        list: Lista de herramientas MCP remotas
    """
    manager = await get_mcp_tools_manager()
    return manager.get_tools()


async def shutdown_mcp_connections():
    """
    Cierra todas las conexiones MCP y libera recursos.
    """
    global _mcp_manager
    if _mcp_manager is not None:
        await _mcp_manager.shutdown()
        _mcp_manager = None
