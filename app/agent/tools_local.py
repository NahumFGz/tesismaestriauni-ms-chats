import os
from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults


def create_tavily_tool():
    """
    Crea y configura la herramienta de búsqueda web de Tavily.

    Returns:
        TavilySearchResults: Herramienta configurada para búsquedas web
    """
    # La API key debe estar configurada en la variable de entorno TAVILY_API_KEY
    tavily_tool = TavilySearchResults(max_results=2)

    return tavily_tool


# Crear la instancia de la herramienta
tavily_search = create_tavily_tool()

# Lista de herramientas disponibles
tools_local_list = [
    tavily_search,
]
