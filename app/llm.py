# llm.py
from typing import Annotated, Optional
from uuid import uuid4

from langchain.chat_models import init_chat_model
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from psycopg_pool import AsyncConnectionPool
from typing_extensions import TypedDict

from app.config import get_settings

settings = get_settings()

# ---------- Estado del Grafo ------------------------------------------------ #


class ChatState(TypedDict):
    """
    - messages: historial (HumanMessage, AIMessage, etc.)
    - topic_decision: 'yes'/'no' indica si la última pregunta
      se considera 'respondible' en el contexto la transparencia gubernamental
    """

    messages: Annotated[list, add_messages]
    topic_decision: str


# ---------- Procesador MCP con Memoria -------------------------------------- #


class MCPQueryProcessor:
    """
    Conecta a varios servidores MCP (vía SSE) y expone `run(query, thread_id)`
    para obtener la respuesta del grafo de LangGraph con memoria persistente.
    """

    SERVERS = {
        "attendance": {"url": settings.MCP_ATTENDANCE_URL, "transport": "sse"},
        "budget": {"url": settings.MCP_BUDGET_URL, "transport": "sse"},
        "voting": {"url": settings.MCP_VOTING_URL, "transport": "sse"},
    }

    def __init__(self):
        self._client: MultiServerMCPClient | None = None
        self._graph = None
        self._memory_saver = None

        # Configuración del LLM para clasificación y respuesta
        self._llm_classifier = None
        self._llm_main = None
        self._llm_fallback = None

    async def start(self) -> None:
        """Abre la conexión y construye el grafo una sola vez."""
        # 1. Inicializar conexión MCP
        self._client = MultiServerMCPClient(self.SERVERS)
        await self._client.__aenter__()  # abre todas las conexiones

        # 2. Obtener herramientas MCP
        tools = self._client.get_tools()
        tools.append(TavilySearchResults(max_results=2))

        # 3. Inicializar modelos
        self._llm_classifier = init_chat_model("openai:gpt-4o-mini", temperature=0.0)
        self._llm_main = init_chat_model("openai:gpt-4o", temperature=0.7)
        self._llm_fallback = init_chat_model("openai:gpt-4o-mini", temperature=0.7)

        # 4. Configurar prompts del sistema
        self._system_message = SystemMessage(
            content=(
                "Eres un asistente conversacional especializado en temas de transparencia gubernamental del Estado peruano. "
                "Respondes de forma clara, respetuosa y profesional, utilizando fuentes confiables cuando es necesario. "
                "Puedes ayudar con información sobre contrataciones públicas, empresas proveedoras del Estado, "
                "asistencia y votaciones del Congreso entre los años 2006 y 2024. "
                "Tu objetivo es facilitar el acceso a datos públicos relevantes para la ciudadanía."
            )
        )

        self._fallback_system_message = SystemMessage(
            content=(
                "Eres un asistente cordial y profesional. Aunque no puedes responder preguntas "
                "fuera del dominio de transparencia gubernamental del Estado peruano, debes explicar "
                "educadamente cuál es tu función y sugerir temas válidos, como contrataciones públicas o votaciones del Congreso. "
                "Si el usuario simplemente saluda, responde con cortesía e invita a hacer una consulta sobre esos temas."
            )
        )

        # 5. Configurar conexión a Postgres  Crear el pool sin abrirlo en el constructor
        pool = AsyncConnectionPool(
            conninfo=settings.database_memory_url,
            max_size=10,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,  # evita errores con statements cacheados
            },
            open=False,  # Importante: no abrir en el constructor
        )
        # Abrir el pool explícitamente
        await pool.open()
        self._memory_saver = AsyncPostgresSaver(pool)

        # 6. Construir el grafo
        self._build_graph(tools)

    def _build_graph(self, tools):
        """Construye el grafo con los nodos necesarios."""

        # Definir nodos
        async def topic_classifier_node(state: ChatState):
            """
            Analiza todo el historial y decide si la última pregunta del usuario
            se puede responder en el contexto de transparencia gubernamental.

            Devuelve {"topic_decision": "yes"} o {"topic_decision": "no"}.
            """
            if not state["messages"]:
                return {"topic_decision": "no"}

            conversation_text = ""
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    conversation_text += f"Usuario: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    conversation_text += f"Asistente: {msg.content}\n"

            classification_prompt = f"""
        Eres un verificador que decide si la última pregunta del usuario puede
        ser respondida en el contexto de transparencia gubernamental del Estado
        peruano, considerando toda la conversación previa.

        - Si la conversación está relacionada con contrataciones públicas, 
          empresas proveedoras del Estado, o actividad parlamentaria (asistencia,
          votaciones, licencias), responde 'yes'.
        - Si no está relacionada con eso, responde 'no'.

        Responde únicamente con 'yes' o 'no'.

        --- CONVERSACIÓN ---
        {conversation_text}
        --- FIN ---
        ¿Se puede responder esta última pregunta dentro del contexto de transparencia gubernamental?
        """

            decision_msg = await self._llm_classifier.ainvoke(
                [HumanMessage(content=classification_prompt)]
            )
            decision_str = decision_msg.content.strip().lower()

            if decision_str.startswith("y"):
                return {"topic_decision": "yes"}
            else:
                return {"topic_decision": "no"}

        def route_topic(state: ChatState) -> str:
            """
            Lee state["topic_decision"] y retorna 'chatbot' o 'fallback'.
            """
            return "chatbot" if state.get("topic_decision", "no").startswith("y") else "fallback"

        async def chatbot_node(state: ChatState):
            """
            Nodo principal:
            - Usa todo el historial + system_message
            - Invoca llm_with_tools (con acceso a herramientas como MCP).
            """
            messages = [self._system_message] + state["messages"]
            llm_with_tools = self._llm_main.bind_tools(tools)
            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        async def fallback_node(state: ChatState):
            """
            Usa un modelo especializado para responder amablemente cuando la consulta
            está fuera de dominio. Informa al usuario sobre el propósito del asistente.
            """
            messages = [self._fallback_system_message] + state["messages"]
            response = await self._llm_fallback.ainvoke(messages)
            return {"messages": [response]}

        # Crear el grafo
        graph_builder = StateGraph(ChatState)

        # Añadir nodos
        graph_builder.add_node("topic_classifier", topic_classifier_node)
        graph_builder.add_node("chatbot", chatbot_node)
        graph_builder.add_node("fallback", fallback_node)
        graph_builder.add_node("tools", ToolNode(tools))

        # Conectar nodos
        graph_builder.add_edge(START, "topic_classifier")
        graph_builder.add_conditional_edges(
            "topic_classifier",
            route_topic,
            {"chatbot": "chatbot", "fallback": "fallback"},
        )
        graph_builder.add_conditional_edges("chatbot", tools_condition)
        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge("fallback", END)

        # Compilar el grafo
        self._graph = graph_builder.compile(checkpointer=self._memory_saver)

    async def stop(self) -> None:
        """Cierra todas las conexiones."""
        if self._client:
            await self._client.__aexit__(None, None, None)

    async def run(self, query: str, thread_id: str = None):
        """
        Ejecuta una consulta en el grafo con memoria persistente.

        Args:
            query: La consulta del usuario
            thread_id: ID del hilo para la memoria. Si es None, se genera uno nuevo.

        Returns:
            Un diccionario con la respuesta y metadatos.
        """
        if not self._graph:
            raise RuntimeError("Processor no inicializado. Llama a start() primero.")

        if thread_id is None:
            thread_id = str(uuid4())

        # Configuración para la memoria
        config = {"configurable": {"thread_id": thread_id}}

        # Preparar el estado inicial
        input_state = {"messages": [HumanMessage(content=query)]}

        # Ejecutar el grafo
        result = await self._graph.ainvoke(input_state, config)

        # Extraer la respuesta del último mensaje del asistente
        response_message = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                response_message = msg.content
                break

        return {
            "response": response_message,
            "thread_id": thread_id,
            "topic_decision": result.get("topic_decision", "unknown"),
        }


# ---------- Instancia global y funciones de utilidad -------------------- #

# Instancia global del procesador (patrón singleton)
_processor: Optional[MCPQueryProcessor] = None


async def get_chat_processor() -> MCPQueryProcessor:
    """
    Obtiene o inicializa el procesador de chat MCP.

    Returns:
        MCPQueryProcessor: Instancia del procesador MCP
    """
    global _processor
    if _processor is None:
        _processor = MCPQueryProcessor()
        await _processor.start()
    return _processor


async def process_chat_query(query: str, thread_id: str = None) -> dict:
    """
    Función de alto nivel para procesar consultas de chat.

    Args:
        query: La consulta del usuario
        thread_id: ID del hilo para mantener contexto entre mensajes

    Returns:
        dict: Respuesta del chat con metadata
    """
    processor = await get_chat_processor()
    return await processor.run(query, thread_id)


async def shutdown_chat_processor():
    """
    Cierra el procesador de chat y libera recursos.
    """
    global _processor
    if _processor is not None:
        await _processor.stop()
        _processor = None
