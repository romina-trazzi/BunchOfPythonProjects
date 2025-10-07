"""
LangChain Agents per RAG avanzato (senza rag_engine)

COS'È
    Un modulo che definisce:
    • Tool personalizzati per interrogare/analizzare la knowledge base (Chroma).
    • 4 agenti specializzati (research, analysis, conversation, coding).
    • Un manager (RAGAgentManager) che costruisce, invoca e logga gli agenti.

NOTE IMPORTANTI
    • In LangChain 0.2.x, BaseTool eredita da Pydantic → i campi vanno dichiarati
      come attributi tipizzati, NON assegnarli in __init__.
    • I tool dichiarano `vector_store_manager: Any` e lo ricevono come kwarg:
          SmartSearchTool(vector_store_manager=...)
          DocumentAnalysisTool(vector_store_manager=...)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

# ---- LangChain core primitives ----
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish

# ---- LangChain agents ----
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool

# ---- Tools "community" & experimental ----
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool

# ---- Config del progetto ----
from .config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Callback per tracciare gli step dell'agente (azioni/finish)
# =============================================================================
class RAGAgentCallbackHandler(BaseCallbackHandler):
    """
    Callback handler che intercetta le azioni dell'agente (tool invocati)
    e la chiusura (risultato finale), per logging e audit.
    """

    def __init__(self) -> None:
        self.actions: List[Dict[str, Any]] = []

    def on_agent_action(self, action: AgentAction, **kwargs) -> Any:
        self.actions.append(
            {
                "tool": action.tool,
                "tool_input": action.tool_input,
                "log": action.log,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.info(f"[Agent] action -> {action.tool} | input: {action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs) -> Any:
        logger.info(f"[Agent] finished -> {finish.return_values}")


# =============================================================================
# Tool custom: DocumentAnalysisTool (Pydantic-safe)
# =============================================================================
class DocumentAnalysisTool(BaseTool):
    """
    Tool che ispeziona la collezione (via vector_store_manager) per
    estrarre statistiche/insight a partire da una query.
    """

    name: str = "document_analysis"
    description: str = "Analizza i documenti nella knowledge base per statistiche e insights"

    # Campo Pydantic dichiarato come attributo (NO __init__)
    vector_store_manager: Any

    class Config:
        # permette di contenere oggetti arbitrari (es. manager non pydantic)
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        try:
            info = self.vector_store_manager.get_collection_info()
            docs = self.vector_store_manager.similarity_search(query, k=10)

            sources: Dict[str, int] = {}
            total_chars = 0
            for doc in docs:
                src = doc.metadata.get("source", "Unknown")
                sources[src] = sources.get(src, 0) + 1
                total_chars += len(doc.page_content)

            analysis = {
                "query_analyzed": query,
                "total_documents_in_collection": info.get("count", 0),
                "relevant_chunks": len(docs),
                "sources_found": len(sources),
                "sources_distribution": sources,
                "average_chunk_length": (total_chars // len(docs)) if docs else 0,
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Errore nell'analisi: {str(e)}"

    async def _arun(self, query: str) -> str:  # pragma: no cover
        raise NotImplementedError("Async not supported for this tool.")


# =============================================================================
# Tool custom: SmartSearchTool (Pydantic-safe)
# =============================================================================
class SmartSearchTool(BaseTool):
    """
    Tool che esegue una 'ricerca intelligente' combinando:
    • similarity search
    • similarity search con score
    e ritorna un JSON con risultati + statistiche.
    """

    name: str = "smart_search"
    description: str = "Esegue ricerche intelligenti usando multiple strategie"

    # Campo Pydantic dichiarato come attributo (NO __init__)
    vector_store_manager: Any

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        try:
            results: Dict[str, Any] = {}

            # Similarity “semplice”
            s_docs = self.vector_store_manager.similarity_search(query, k=5)
            results["similarity_search"] = [
                {
                    "content": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "relevance": "high",
                }
                for doc in s_docs
            ]

            # Similarity con score
            s_scored = self.vector_store_manager.similarity_search_with_score(query, k=3)
            results["scored_search"] = [
                {
                    "content": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "score": float(score),
                }
                for doc, score in s_scored
            ]

            # Statistiche base
            results["search_stats"] = {
                "query": query,
                "total_results": len(s_docs),
                "unique_sources": len({doc.metadata.get("source", "Unknown") for doc in s_docs}),
                "timestamp": datetime.now().isoformat(),
            }

            return json.dumps(results, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Errore nella ricerca: {str(e)}"

    async def _arun(self, query: str) -> str:  # pragma: no cover
        raise NotImplementedError("Async not supported for this tool.")


# =============================================================================
# Manager degli agenti (creazione, invocazione, helper)
# =============================================================================
class RAGAgentManager:
    """
    Orchestratore che costruisce e gestisce 4 agenti:
    • research: ricerche/analisi su KB e web
    • analysis: statistiche e sintesi su KB
    • conversation: assistente conversazionale con accesso alla KB
    • coding: REPL Python + ricerca codice (se abilitato)
    """

    def __init__(self, llm, vector_store_manager, memory_manager) -> None:
        self.llm = llm
        self.vector_store_manager = vector_store_manager
        self.memory_manager = memory_manager

        self.agents: Dict[str, AgentExecutor] = {}
        self.callback_handler = RAGAgentCallbackHandler()

        self._setup_agents()
        logger.info("RAG Agent Manager initialized")

    # ------------------------------------------------------------------ #
    # Costruzione agenti
    # ------------------------------------------------------------------ #
    def _setup_agents(self) -> None:
        """Crea e registra gli agenti disponibili in base ai feature flag."""
        self.agents["research"] = self._create_research_agent()
        self.agents["analysis"] = self._create_analysis_agent()
        self.agents["conversation"] = self._create_conversation_agent()

        if settings.enable_code_execution:
            self.agents["coding"] = self._create_coding_agent()

    def _create_research_agent(self) -> AgentExecutor:
        """Agente orientato alla ricerca KB + (opzionale) web."""
        tools: List[Any] = [
            SmartSearchTool(vector_store_manager=self.vector_store_manager),
            DocumentAnalysisTool(vector_store_manager=self.vector_store_manager),
        ]
        if settings.enable_web_search:
            tools.append(
                Tool(
                    name="web_search",
                    description="Cerca informazioni su internet quando la knowledge base non è sufficiente",
                    func=self._web_search_wrapper,
                )
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Sei un agente di ricerca esperto specializzato nell'analisi di documenti e knowledge base.\n"
                        "Capacità:\n"
                        "- Ricerca intelligente nei documenti\n"
                        "- Analisi statistica della knowledge base\n"
                        "- Ricerca web per informazioni aggiuntive\n\n"
                        "Fornisci risposte dettagliate e ben strutturate. Cita le fonti quando possibile."
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            callbacks=[self.callback_handler],
        )

    def _create_analysis_agent(self) -> AgentExecutor:
        """Agente focalizzato su insight/riassunti e statistiche sul contenuto della KB."""
        tools: List[Any] = [
            DocumentAnalysisTool(vector_store_manager=self.vector_store_manager),
            Tool(
                name="collection_stats",
                description="Ottieni statistiche dettagliate sulla collezione di documenti",
                func=self._get_collection_stats,
            ),
            Tool(
                name="content_summary",
                description="Crea un riassunto del contenuto della knowledge base (su un topic)",
                func=self._create_content_summary,
            ),
        ]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Sei un agente di analisi specializzato nell'analisi di contenuti e knowledge base.\n"
                        "Capacità:\n"
                        "- Analisi statistica dei documenti\n"
                        "- Creazione di riassunti e insights\n"
                        "- Identificazione di pattern nei contenuti\n\n"
                        "Fornisci analisi dettagliate e actionable insights."
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            callbacks=[self.callback_handler],
        )

    def _create_conversation_agent(self) -> AgentExecutor:
        """Agente conversazionale con accesso alla KB e alla history di sessione."""
        tools: List[Any] = [
            Tool(
                name="search_context",
                description="Cerca contesto rilevante nella knowledge base",
                func=lambda q: self._search_context(q),
            ),
            Tool(
                name="conversation_history",
                description="Accedi alla storia della conversazione corrente",
                func=self._get_conversation_context,
            ),
        ]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Sei un assistente conversazionale avanzato con accesso a una knowledge base.\n"
                        "Capacità:\n"
                        "- Conversazioni naturali e contestuali\n"
                        "- Accesso alla knowledge base\n"
                        "- Memoria delle conversazioni precedenti\n\n"
                        "Mantieni un tono professionale ma amichevole."
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            callbacks=[self.callback_handler],
        )

    def _create_coding_agent(self) -> AgentExecutor:
        """Agente con Python REPL + ricerca codice (solo se abilitato)."""
        tools: List[Any] = [
            PythonREPLTool(),
            Tool(
                name="code_search",
                description="Cerca frammenti di codice o documentazione tecnica nella KB",
                func=self._search_code,
            ),
        ]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Sei un agente di programmazione esperto con accesso a un Python REPL.\n"
                        "Capacità:\n"
                        "- Esecuzione di codice Python\n"
                        "- Analisi di dati e debugging\n"
                        "- Ricerca in documentazione tecnica\n\n"
                        "ATTENZIONE: Esegui solo codice sicuro e non dannoso."
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            callbacks=[self.callback_handler],
        )

    # ------------------------------------------------------------------ #
    # Helper interni (tool functions)
    # ------------------------------------------------------------------ #
    def _web_search_wrapper(self, query: str) -> str:
        """Wrapper minimale per la ricerca web (DuckDuckGo)."""
        try:
            search = DuckDuckGoSearchRun()
            results = search.run(query)
            return f"Risultati ricerca web per '{query}':\n{results}"
        except Exception as e:
            return f"Errore nella ricerca web: {str(e)}"

    def _get_collection_stats(self, _: str) -> str:
        """Ritorna info collezione (JSON)."""
        try:
            info = self.vector_store_manager.get_collection_info()
            return json.dumps(info, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Errore nel recupero statistiche: {str(e)}"

    def _create_content_summary(self, topic: str) -> str:
        """Riassunto strutturale della KB per un dato topic."""
        try:
            docs = self.vector_store_manager.similarity_search(topic, k=10)
            if not docs:
                return f"Nessun contenuto trovato per il topic: {topic}"

            sources = set()
            total_len = 0
            for doc in docs:
                sources.add(doc.metadata.get("source", "Unknown"))
                total_len += len(doc.page_content)

            summary = {
                "topic": topic,
                "sources_count": len(sources),
                "sources": sorted(list(sources)),
                "content_length": total_len,
                "documents_analyzed": len(docs),
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(summary, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Errore nella creazione del riassunto: {str(e)}"

    def _search_context(self, query: str) -> str:
        """Estrae 3 snippet di contesto dalla KB, per aiutare la conversazione."""
        try:
            docs = self.vector_store_manager.similarity_search(query, k=3)
            lines = ["Contesto rilevante:"]
            for i, doc in enumerate(docs, 1):
                snippet = (doc.page_content[:300] + "...") if len(doc.page_content) > 300 else doc.page_content
                lines.append(f"{i}. {snippet}\n   Fonte: {doc.metadata.get('source', 'N/A')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Errore nella ricerca del contesto: {str(e)}"

    def _get_conversation_context(self, session_id: str) -> str:
        """Ritorna gli ultimi messaggi della sessione (via MemoryManager)."""
        try:
            if not self.memory_manager:
                return "Memoria disabilitata."
            session_info = self.memory_manager.get_session_info(session_id)
            if not session_info.get("exists"):
                return "Nessuna conversazione precedente trovata."

            lines = [f"Conversazione con {session_info['message_count']} messaggi (ultimi 5):"]
            for msg in session_info.get("messages", [])[-5:]:
                lines.append(f"- {msg['type']}: {msg['content']}")
            return "\n".join(lines)
        except Exception as e:
            return f"Errore nel recupero del contesto: {str(e)}"

    def _search_code(self, query: str) -> str:
        """Cerca nella KB contenuti che 'somigliano' a codice (euristico)."""
        try:
            docs = self.vector_store_manager.similarity_search(f"code programming {query}", k=5)
            lines = ["Codice e documentazione trovati:"]
            for doc in docs:
                text = doc.page_content.lower()
                if any(kw in text for kw in ("def ", "class ", "import ", "function", "method")):
                    snippet = (doc.page_content[:500] + "...") if len(doc.page_content) > 500 else doc.page_content
                    lines.append(f"Fonte: {doc.metadata.get('source', 'N/A')}\n{snippet}\n")
            return "\n".join(lines)
        except Exception as e:
            return f"Errore nella ricerca del codice: {str(e)}"

    # ------------------------------------------------------------------ #
    # API pubblica del manager
    # ------------------------------------------------------------------ #
    def execute_agent(self, agent_type: str, query: str, session_id: str = "default") -> Dict[str, Any]:
        """Esegue un agente specifico e ritorna output + passi eseguiti."""
        if agent_type not in self.agents:
            raise ValueError(f"Agent type '{agent_type}' not found. Disponibili: {list(self.agents)}")

        agent = self.agents[agent_type]
        self.callback_handler.actions = []  # reset step

        result = agent.invoke({"input": query}, config={"configurable": {"session_id": session_id}})

        return {
            "agent_type": agent_type,
            "query": query,
            "output": result["output"] if isinstance(result, dict) else str(result),
            "actions_taken": list(self.callback_handler.actions),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

    # Wrapper comodi
    def conversation_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        return self.execute_agent("conversation", query, session_id)

    def research_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        return self.execute_agent("research", query, session_id)

    def analysis_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        return self.execute_agent("analysis", query, session_id)

    def coding_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        if "coding" not in self.agents:
            raise ValueError("L'agente 'coding' non è abilitato (ENABLE_CODE_EXECUTION=false).")
        return self.execute_agent("coding", query, session_id)

    def list_available_agents(self) -> List[Dict[str, str]]:
        """Ritorna la lista degli agenti realmente disponibili."""
        items: List[Dict[str, str]] = [
            {"name": "research", "description": "Agente per ricerca e analisi avanzata"},
            {"name": "analysis", "description": "Agente per analisi statistica e insights"},
            {"name": "conversation", "description": "Agente conversazionale avanzato"},
        ]
        if "coding" in self.agents:
            items.append({"name": "coding", "description": "Agente per programmazione e analisi tecnica (REPL)"})
        return items
