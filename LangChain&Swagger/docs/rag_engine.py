"""
RAG Engine with Claude Sonnet integration using LangChain

COS'È:
    Il cuore del sistema: orchestra LLM (Claude), retriever (Chroma),
    catene LangChain (LCEL), memoria conversazionale e (opzionalmente) agenti.

COSA FA (in sintesi):
    - Inizializza LLM (Claude Sonnet) e il Vector Store (Chroma + embeddings HF).
    - Prepara il retriever e due catene:
        * history-aware retriever (contestualizza la query con la chat history)
        * question-answer chain (risponde usando i documenti recuperati)
    - Espone metodi di alto livello per:
        * indicizzare documenti (delegando a DocumentProcessor + VectorStoreManager)
        * fare query conversazionali (`query`)
        * eseguire query avanzate con agenti (`query_with_agent`)
        * streammare la risposta (`stream_query`)
        * simili, info collezione, pulizia, gestione sessioni/memoria.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---- LangChain Core / LCEL ----
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

# ---- LangChain LLM (Anthropic) ----
from langchain_anthropic import ChatAnthropic

# ---- LangChain Chains / QA / Retrieval ----
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain

# ---- Memoria conversazionale (fallback legacy) ----
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory

# ---- Tipi Documento ----
from langchain.schema import Document

# ---- Moduli locali ----
from ..src.config import settings
from ..src.document_processor import DocumentProcessor
from ..src.vector_store import VectorStoreManager
from ..src.memory_manager import MemoryManager
from ..src.agents import RAGAgentManager

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    COS'È:
        Il motore RAG avanzato che integra LLM, retriever, memoria e agenti.

    FLUSSO PRINCIPALE:
        - __init__() richiama:
            * self.vector_store_manager.initialize_vector_store()
            * self._initialize_claude()
            * self._setup_chains()
            * RAGAgentManager (se abilitato)
    """

    def __init__(self) -> None:
        # --- Componenti principali (inizializzati step-by-step) ---
        self.llm: Optional[ChatAnthropic] = None
        self.retrieval_chain = None         # chain che restituisce {"answer", "context"}
        self.conversational_chain = None    # retrieval_chain + MessageHistory
        self.vector_store_manager = VectorStoreManager()
        self.document_processor = DocumentProcessor()

        # Memoria conversazionale (due modalità: manager avanzato o fallback legacy)
        self.memory_manager: Optional[MemoryManager] = MemoryManager() if settings.enable_memory else None
        self.agent_manager: Optional[RAGAgentManager] = None  # creato dopo LLM

        # Fallback legacy (se memory manager non è abilitato)
        self.memory = ConversationBufferWindowMemory(
            k=max(1, settings.max_tokens // 100),
            return_messages=True,
            memory_key="chat_history",
        )
        self.chat_history = ChatMessageHistory()

        # --- Inizializza il Vector Store (Chroma) ---
        self.vector_store_manager.initialize_vector_store()

        # --- Inizializza LLM e catene LCEL ---
        self._initialize_claude()
        self._setup_chains()

        # --- Inizializza Agent Manager (opzionale) ---
        if settings.enable_agents:
            self.agent_manager = RAGAgentManager(
                self.llm, self.vector_store_manager, self.memory_manager
            )

        logger.info("Advanced RAG Engine initialized successfully")

    # -------------------------------------------------------------------------
    # INIZIALIZZAZIONE LLM
    # -------------------------------------------------------------------------
    def _initialize_claude(self) -> ChatAnthropic:
        """
        COSA FA:
            Inizializza il client Claude Sonnet usando la chiave da settings.

        RETURN:
            Istanza di ChatAnthropic pronta all’uso.
        """
        try:
            self.llm = ChatAnthropic(
                anthropic_api_key=settings.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )
            logger.info("Claude Sonnet model initialized successfully")
            return self.llm
        except Exception as e:
            logger.error(f"Error initializing Claude Sonnet: {str(e)}")
            raise

    # -------------------------------------------------------------------------
    # SETUP CATENE (LCEL)
    # -------------------------------------------------------------------------
    def _setup_chains(self) -> None:
        """
        COSA FA:
            Prepara il pipeline RAG in due step:
            1) history-aware retriever (contestualizzazione della domanda)
            2) question-answer chain (usa i documenti recuperati per rispondere)
            Infine avvolge il tutto con RunnableWithMessageHistory per sessioni.
        """
        try:
            # --- Prompt per contestualizzare la domanda con la chat history ---
            contextualize_q_system_prompt = (
                "Dato un chat history e l'ultima domanda dell'utente che potrebbe "
                "fare riferimento al contesto nella chat history, formula una domanda "
                "standalone comprensibile senza la chat history. NON rispondere; "
                "riformula solo se necessario."
            )
            contextualize_q_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # --- Retriever consapevole della storia ---
            retriever = self.vector_store_manager.get_retriever(
                search_kwargs={"k": settings.top_k_results}
            )
            self.history_aware_retriever = create_history_aware_retriever(
                self.llm, retriever, contextualize_q_prompt
            )

            # --- Prompt QA finale (usa {context} recuperato) ---
            qa_system_prompt = (
                "Sei un assistente AI che risponde basandosi sul contesto fornito.\n\n"
                "Usa i pezzi di contesto recuperato per rispondere alla domanda.\n"
                "Se non conosci la risposta, dillo chiaramente. Rispondi in modo conciso.\n\n"
                "{context}"
            )
            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", qa_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # --- Catena di answer sui documenti (stuff chain) ---
            question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

            # --- Catena RAG (retrieval + QA) che emette {"answer", "context"} ---
            self.retrieval_chain = create_retrieval_chain(
                self.history_aware_retriever, question_answer_chain
            )

            # --- Wrapping con memoria conversazionale (sessioni) ---
            if self.memory_manager:
                self.conversational_chain = RunnableWithMessageHistory(
                    self.retrieval_chain,
                    # Funzione che, dato un session_id, ritorna l’oggetto chat history
                    lambda session_id: self.memory_manager.get_session_history(session_id),
                    input_messages_key="input",
                    history_messages_key="chat_history",
                )
            else:
                # Fallback: usa una history in-memory unica
                self.conversational_chain = RunnableWithMessageHistory(
                    self.retrieval_chain,
                    lambda session_id: self.chat_history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                )

            logger.info("LangChain chains setup completed")

        except Exception as e:
            logger.error(f"Error setting up chains: {str(e)}")
            raise

    # -------------------------------------------------------------------------
    # INDICIZZAZIONE DOCUMENTI
    # -------------------------------------------------------------------------
    def add_documents_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        COSA FA:
            Esegue la pipeline completa su UN file: load -> split -> add to vector store.
            Ritorna un dizionario con esito, ids, tempi e metadati sorgente.
        """
        try:
            start = datetime.now()

            # 1) Carica + split
            documents = self.document_processor.process_documents(file_path, is_directory=False)
            if not documents:
                return {"success": False, "message": "No documents were processed", "documents_added": 0}

            # 2) Indicizza su Chroma
            ids = self.vector_store_manager.add_documents(documents)

            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "message": f"Successfully added {len(documents)} document chunks",
                "documents_added": len(documents),
                "document_ids": ids,
                "processing_time_seconds": elapsed,
                "source_file": file_path,
            }
        except Exception as e:
            logger.error(f"Error adding documents from file {file_path}: {str(e)}")
            return {"success": False, "message": f"Error processing file: {e}", "documents_added": 0}

    def add_documents_from_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        COSA FA:
            Pipeline su una DIRECTORY intera: load -> split -> add to vector store.
        """
        try:
            start = datetime.now()

            documents = self.document_processor.process_documents(directory_path, is_directory=True)
            if not documents:
                return {"success": False, "message": "No documents were processed", "documents_added": 0}

            ids = self.vector_store_manager.add_documents(documents)

            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "message": f"Successfully added {len(documents)} document chunks",
                "documents_added": len(documents),
                "document_ids": ids,
                "processing_time_seconds": elapsed,
                "source_directory": directory_path,
            }
        except Exception as e:
            logger.error(f"Error adding documents from directory {directory_path}: {e}")
            return {"success": False, "message": f"Error processing directory: {e}", "documents_added": 0}

    # -------------------------------------------------------------------------
    # QUERY CONVERSAZIONALE (RAG)
    # -------------------------------------------------------------------------
    def query(
        self,
        question: str,
        include_sources: bool = True,
        k: Optional[int] = None,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """
        COSA FA:
            Esegue una query RAG con memoria di sessione.
            Ritorna un payload compatibile con `QueryResponse`.

        PARAMS:
            question: domanda dell'utente.
            include_sources: se includere i documenti usati nel contesto.
            k: limita il numero di sorgenti restituite (se None usa tutte quelle presenti).
            session_id: id sessione conversazionale.
        """
        try:
            if not self.conversational_chain:
                raise ValueError("Conversational chain not initialized")

            start = datetime.now()

            result = self.conversational_chain.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}},
            )

            # Il retrieval_chain emette un dict tipo {"answer": str, "context": List[Document]}
            answer = result["answer"] if isinstance(result, dict) else str(result)

            sources = None
            num_sources = None
            if include_sources:
                ctx: List[Document] = result.get("context", [])
                if k is not None:
                    ctx = ctx[:k]
                sources = [
                    {
                        "content": d.page_content,
                        "metadata": d.metadata,
                        "source": d.metadata.get("source", "Unknown"),
                    }
                    for d in ctx
                ]
                num_sources = len(sources)

            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "response_time_seconds": elapsed,
                "timestamp": datetime.now().isoformat(),
                "sources": sources,
                "num_sources": num_sources,
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "question": question,
                "answer": None,
                "response_time_seconds": 0.0,
                "timestamp": datetime.now().isoformat(),
                "message": str(e),
            }

    # -------------------------------------------------------------------------
    # STREAMING DELLA RISPOSTA (per endpoint SSE)
    # -------------------------------------------------------------------------
    def stream_query(self, question: str, session_id: str = "default"):
        """
        COSA FA:
            Esegue lo streaming della risposta generata dall’LLM.
            Emette piccoli dizionari (es. {"delta": "..."}), adatti a SSE.
        """
        if not self.conversational_chain:
            raise ValueError("Conversational chain not initialized")

        for chunk in self.conversational_chain.stream(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        ):
            if "answer" in chunk:
                yield {"delta": chunk["answer"]}

    # -------------------------------------------------------------------------
    # QUERY CON AGENTI (ricerca/analisi/coding/conversation)
    # -------------------------------------------------------------------------
    def query_with_agent(
        self, query: str, session_id: str = "default", agent_type: str = "conversation"
    ) -> Dict[str, Any]:
        """
        COSA FA:
            Esegue la query usando un agente specializzato (se abilitati).
            Se agenti disabilitati, fa fallback su `query()` classica.
        """
        try:
            # Fallback se gli agenti non sono disponibili
            if not self.agent_manager:
                fb = self.query(query, session_id=session_id)
                return {
                    "answer": fb.get("answer", ""),
                    "agent_type": "conversation",
                    "agent_steps": [],
                    "session_id": session_id,
                    "timestamp": fb.get("timestamp", datetime.now().isoformat()),
                }

            # Esecuzione agente tramite manager (torna output + azioni)
            res = self.agent_manager.execute_agent(agent_type, query, session_id)
            return {
                "answer": res.get("output", ""),
                "agent_type": agent_type,
                "agent_steps": res.get("actions_taken", []),
                "session_id": session_id,
                "timestamp": res.get("timestamp", datetime.now().isoformat()),
            }

        except Exception as e:
            logger.error(f"Error in agent query: {str(e)}")
            return {
                "answer": f"Errore: {str(e)}",
                "agent_type": agent_type,
                "agent_steps": [],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }

    # -------------------------------------------------------------------------
    # FUNZIONI DI SUPPORTO: SIMILAR, INFO, CLEAR
    # -------------------------------------------------------------------------
    def get_similar_documents(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        COSA FA:
            Esegue una similarity search (con punteggio) e ritorna un elenco serializzabile.
        """
        try:
            k = k or settings.top_k_results
            results = self.vector_store_manager.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score),
                    "source": doc.metadata.get("source", "Unknown"),
                }
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Error getting similar documents: {str(e)}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """
        COSA FA:
            Raccoglie info dal VectorStore e aggiunge parametri RAG/LLM utili.
        """
        try:
            info = self.vector_store_manager.get_collection_info()
            info.update(
                {
                    "model": "claude-3-sonnet-20240229",
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                    "top_k_results": settings.top_k_results,
                }
            )
            return info
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}

    def clear_documents(self) -> Dict[str, Any]:
        """
        COSA FA:
            Svuota la collezione corrente e ricostruisce le catene (retriever invariato).
        """
        try:
            result = self.vector_store_manager.clear_collection()
            # Le catene puntano al retriever; dopo lo svuotamento non servirebbe ricrearle,
            # ma lo facciamo per coerenza.
            self._setup_chains()
            logger.info("Documents cleared successfully")
            return result
        except Exception as e:
            logger.error(f"Error clearing documents: {str(e)}")
            return {"success": False, "message": str(e)}

    # -------------------------------------------------------------------------
    # SESSIONI / MEMORIA
    # -------------------------------------------------------------------------
    def clear_conversation_history(self, session_id: str = "default") -> Dict[str, Any]:
        """
        COSA FA:
            Svuota la storia della conversazione per una sessione specifica.
        """
        try:
            if self.memory_manager:
                self.memory_manager.clear_session(session_id)
            else:
                self.chat_history.clear()
                self.memory.clear()
            logger.info(f"Conversation history cleared for session: {session_id}")
            return {
                "success": True,
                "message": f"Conversation history cleared for session: {session_id}",
                "session_id": session_id,
            }
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_conversation_history(self, session_id: str = "default") -> Dict[str, Any]:
        """
        COSA FA:
            Ritorna l’elenco (serializzabile) dei messaggi per la sessione indicata.
        """
        try:
            if self.memory_manager:
                session_history = self.memory_manager.get_session_history(session_id)
                messages = session_history.messages
            else:
                messages = self.chat_history.messages

            history: List[Dict[str, str]] = []
            for msg in messages:
                # I messaggi possono essere HumanMessage o AIMessage
                mtype = getattr(msg, "type", None) or msg.__class__.__name__.lower()
                content = getattr(msg, "content", "")
                # Normalizza il tipo ai valori "human"/"ai"
                if mtype.startswith("human"):
                    history.append({"type": "human", "content": content})
                else:
                    history.append({"type": "ai", "content": content})

            return {
                "success": True,
                "session_id": session_id,
                "history": history,
                "message_count": len(history),
            }
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_session_list(self) -> Dict[str, Any]:
        """
        COSA FA:
            Ritorna la lista delle sessioni attive (solo ID), più il conteggio.
        """
        try:
            if self.memory_manager:
                infos = self.memory_manager.list_active_sessions()
                sessions = [info["session_id"] for info in infos if info.get("exists", True)]
            else:
                sessions = ["default"]
            return {"success": True, "sessions": sessions, "session_count": len(sessions)}
        except Exception as e:
            logger.error(f"Error getting session list: {str(e)}")
            return {"success": False, "sessions": [], "session_count": 0, "message": str(e)}

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        COSA FA:
            Cancella una sessione (e file collegato) se il MemoryManager è attivo,
            altrimenti gestisce solo la "default" (legacy).
        """
        try:
            if self.memory_manager:
                ok = self.memory_manager.clear_session(session_id)
                return {
                    "success": ok,
                    "message": f"{'Deleted' if ok else 'Not found'} session {session_id}",
                    "session_id": session_id,
                }
            if session_id == "default":
                self.chat_history.clear()
                self.memory.clear()
                return {"success": True, "message": "Default session cleared", "session_id": session_id}
            return {"success": False, "message": "Session management not available in legacy mode", "session_id": session_id}
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return {"success": False, "message": str(e), "session_id": session_id}

    # -------------------------------------------------------------------------
    # CUSTOM CHAIN (prompt fornito dall’utente)
    # -------------------------------------------------------------------------
    def create_custom_chain(self, prompt_template: str, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        COSA FA:
            Crea al volo una catena con un prompt "system" custom e la esegue.
            Ritorna direttamente la risposta (non l'oggetto chain).

        PARAMS:
            prompt_template: contenuto del messaggio di sistema (puoi inserire linee guida).
            query: input dell’utente per questa catena custom.
            session_id: sessione su cui mantenere la history.
        """
        try:
            custom_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", prompt_template),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )
            chain = custom_prompt | self.llm | StrOutputParser()

            conv = RunnableWithMessageHistory(
                chain,
                lambda sid: self.memory_manager.get_session_history(sid) if self.memory_manager else self.chat_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )

            out = conv.invoke({"input": query}, config={"configurable": {"session_id": session_id}})
            return {
                "answer": out,
                "prompt_used": prompt_template,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in custom chain: {str(e)}")
            return {
                "answer": f"Errore: {str(e)}",
                "prompt_used": prompt_template,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }