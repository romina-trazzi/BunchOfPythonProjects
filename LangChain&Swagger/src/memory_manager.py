"""
Memory Manager per LangChain RAG/Agents

COS'È:
    Un modulo che gestisce la memoria conversazionale a livello di sessione:
    - salvataggio/lettura dei messaggi su file JSON (persistenza semplice)
    - API per ottenere info di sessione, esportare/importare, pulire scadute
    - (opzionale) factory per oggetti Memory di LangChain (Buffer/Summary)

COSA FA:
    - Fornisce una classe SessionChatMessageHistory (compatibile con LangChain)
      che legge/scrive i messaggi di una sessione su disco.
    - Fornisce MemoryManager che crea/gestisce più SessionChatMessageHistory,
      con timeout, lista sessioni, export/import e pulizia.
    - Non dipende da rag_engine: può essere usato dagli agenti o da altre parti.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Messaggi e interfacce "core" di LangChain 0.2.x
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

# (Opzionale) tipi Memory di LangChain; li importiamo lazy/soft per evitare hard-deps
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory  # type: ignore
except Exception:  # pragma: no cover - se non presenti, abilitiamo la modalità "solo file"
    ConversationBufferWindowMemory = None  # type: ignore
    ConversationSummaryBufferMemory = None  # type: ignore

from .config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# SessionChatMessageHistory
# -----------------------------------------------------------------------------
# COS'È:
#     Implementazione concreta di BaseChatMessageHistory che persiste i messaggi
#     su file JSON (data/sessions/<session_id>.json).
#
# COSA FA:
#     - Carica i messaggi all'avvio (se il file esiste).
#     - Salva ad ogni aggiunta/clear.
#     - Espone property `messages` come lista di BaseMessage (Human/AI).
# =============================================================================
class SessionChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, file_path: Optional[str] = None) -> None:
        self.session_id = session_id
        self.file_path = file_path or os.path.join("data", "sessions", f"{session_id}.json")
        self._messages: List[BaseMessage] = []
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._load_messages()

    # -------------------------- I/O su file JSON -------------------------- #
    def _load_messages(self) -> None:
        """Carica i messaggi da file (se presente)."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for msg in data.get("messages", []):
                    role = msg.get("type")
                    content = msg.get("content", "")
                    if role == "human":
                        self._messages.append(HumanMessage(content=content))
                    elif role == "ai":
                        self._messages.append(AIMessage(content=content))
            logger.debug(f"[Session {self.session_id}] loaded {len(self._messages)} messages")
        except Exception as e:
            logger.error(f"Error loading messages for session {self.session_id}: {e}")

    def _save_messages(self) -> None:
        """Salva i messaggi correnti su file (formato JSON)."""
        try:
            data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "messages": [],
            }
            for msg in self._messages:
                if isinstance(msg, HumanMessage):
                    data["messages"].append({"type": "human", "content": msg.content, "ts": datetime.now().isoformat()})
                elif isinstance(msg, AIMessage):
                    data["messages"].append({"type": "ai", "content": msg.content, "ts": datetime.now().isoformat()})
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving messages for session {self.session_id}: {e}")

    # --------------------------- API richieste da LC ---------------------- #
    @property
    def messages(self) -> List[BaseMessage]:
        """Ritorna la lista dei messaggi (Human/AI)."""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """Aggiunge un messaggio e persiste su file."""
        self._messages.append(message)
        self._save_messages()

    def clear(self) -> None:
        """Svuota la conversazione (e aggiorna il file)."""
        self._messages.clear()
        self._save_messages()

    # --------------------------- helpers comodi --------------------------- #
    def add_user_message(self, content: str) -> None:
        self.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        self.add_message(AIMessage(content=content))


# =============================================================================
# MemoryManager
# -----------------------------------------------------------------------------
# COS'È:
#     Un orchestratore che gestisce più sessioni (ognuna con la propria history),
#     scadenze/timeout, creazione di Memory di LangChain (opzionale), export/import.
#
# COSA FA:
#     - get_session_history(session_id) -> SessionChatMessageHistory
#     - get_session_info(session_id)    -> dict riassuntivo
#     - list_active_sessions()          -> lista informazioni sessioni attive
#     - clear_session(session_id)       -> reset e rimozione file
#     - cleanup_expired_sessions()      -> pulizia automatica delle scadute
#     - export_session / import_session -> backup/restore semplice
#     - create_memory(...)              -> factory per oggetti Memory LC (facoltativo)
# =============================================================================
class MemoryManager:
    def __init__(self) -> None:
        # tutte le sessioni vive nella memoria del processo
        self.sessions: Dict[str, SessionChatMessageHistory] = {}
        # metadati di configurazione per sessione (tipo di memory, ecc.)
        self.memory_configs: Dict[str, Dict[str, Any]] = {}
        # mappa session_id -> deadline (per timeout)
        self.session_timeouts: Dict[str, datetime] = {}
        # timeout di default (dalle impostazioni)
        self.default_timeout = timedelta(hours=settings.session_timeout_hours)

        os.makedirs(os.path.join("data", "sessions"), exist_ok=True)
        logger.info("Memory Manager initialized")

    # --------------------------- gestione sessioni ------------------------ #
    def get_session_history(self, session_id: str) -> SessionChatMessageHistory:
        """
        Ritorna (o crea) la history per una sessione.
        Aggiorna il timeout (sliding window) ad ogni accesso.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionChatMessageHistory(session_id)
        # refresh del timeout
        self.session_timeouts[session_id] = datetime.now() + self.default_timeout
        return self.sessions[session_id]

    def clear_session(self, session_id: str) -> bool:
        """
        Cancella completamente una sessione:
        - svuota la history
        - rimuove riferimenti interni
        - elimina il file su disco
        """
        try:
            if session_id in self.sessions:
                self.sessions[session_id].clear()
                del self.sessions[session_id]
            self.memory_configs.pop(session_id, None)
            self.session_timeouts.pop(session_id, None)

            file_path = os.path.join("data", "sessions", f"{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)

            logger.info(f"Session {session_id} cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Cancella le sessioni scadute (in base a session_timeouts).
        Ritorna il numero di sessioni ripulite.
        """
        now = datetime.now()
        expired = [sid for sid, deadline in self.session_timeouts.items() if now > deadline]
        for sid in expired:
            self.clear_session(sid)
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions: {expired}")
        return len(expired)

    # ----------------------------- introspezione -------------------------- #
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Ritorna un riassunto serializzabile della sessione:
        - exists, message_count, ultimi messaggi (max 10, tronchi a 100 char), ecc.
        """
        if session_id not in self.sessions:
            # Se il file esiste ma non è in cache, carichiamo un'istanza temporanea
            file_path = os.path.join("data", "sessions", f"{session_id}.json")
            if not os.path.exists(file_path):
                return {"exists": False, "session_id": session_id}

            temp = SessionChatMessageHistory(session_id)
            msgs = temp.messages
            exists = True
        else:
            msgs = self.sessions[session_id].messages
            exists = True

        cfg = self.memory_configs.get(session_id, {})
        expires_at = self.session_timeouts.get(session_id, datetime.now())
        return {
            "exists": exists,
            "session_id": session_id,
            "message_count": len(msgs),
            "memory_type": cfg.get("type", "buffer_window"),
            "created_at": cfg.get("created_at"),
            "expires_at": expires_at.isoformat(),
            "messages": [
                {
                    "type": "human" if isinstance(m, HumanMessage) else "ai",
                    "content": (m.content[:100] + "...") if len(m.content) > 100 else m.content,
                }
                for m in msgs[-10:]  # ultimi 10
            ],
        }

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Ritorna una lista di dict con informazioni sulle sessioni attive in memoria.
        (Utile per API admin o pagine di diagnostica.)
        """
        return [self.get_session_info(sid) for sid in self.sessions.keys()]

    def get_all_sessions(self) -> List[str]:
        """
        Ritorna l'elenco di TUTTE le sessioni visibili:
        - quelle in memoria
        - quelle presenti su disco nella cartella data/sessions
        """
        disk = set()
        try:
            for name in os.listdir(os.path.join("data", "sessions")):
                if name.endswith(".json"):
                    disk.add(os.path.splitext(name)[0])
        except Exception:
            pass
        mem = set(self.sessions.keys())
        return sorted(list(disk.union(mem)))

    # ------------------------- export / import ---------------------------- #
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Esporta tutti i messaggi della sessione in un dict JSON-serializable.
        """
        if session_id not in self.sessions:
            # Carica da file se non è in RAM
            file_path = os.path.join("data", "sessions", f"{session_id}.json")
            if not os.path.exists(file_path):
                return None
            tmp = SessionChatMessageHistory(session_id)
            msgs = tmp.messages
        else:
            msgs = self.sessions[session_id].messages

        return {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "message_count": len(msgs),
            "messages": [
                {
                    "type": "human" if isinstance(m, HumanMessage) else "ai",
                    "content": m.content,
                    "timestamp": datetime.now().isoformat(),  # placeholder timestamp
                }
                for m in msgs
            ],
        }

    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Importa una sessione da un dict (formato compatibile con export_session).
        Sostituisce l'eventuale sessione esistente con i messaggi forniti.
        """
        try:
            session_id = session_data["session_id"]
            hist = self.get_session_history(session_id)  # crea/recupera
            # reset
            hist.clear()
            # importa messaggi
            for msg in session_data.get("messages", []):
                if msg.get("type") == "human":
                    hist.add_user_message(msg.get("content", ""))
                elif msg.get("type") == "ai":
                    hist.add_ai_message(msg.get("content", ""))
            logger.info(f"Session {session_id} imported successfully")
            return True
        except Exception as e:
            logger.error(f"Error importing session: {e}")
            return False

    # -------------------------- factory per Memory ------------------------ #
    def create_memory(self, session_id: str, memory_type: str = "buffer_window", *, llm: Any = None) -> Any:
        """
        Crea un oggetto Memory di LangChain associato ad una sessione.

        memory_type:
            - "buffer_window": finestra degli ultimi k messaggi (ConversationBufferWindowMemory)
            - "summary_buffer": riassume e compatta la history (ConversationSummaryBufferMemory) → richiede `llm`

        NOTE:
            - Se i moduli Memory non sono installati, solleva un ValueError.
            - Questo è opzionale: gli agenti possono usare direttamente get_session_history.
        """
        # Verifica dipendenze opzionali
        if memory_type == "buffer_window":
            if ConversationBufferWindowMemory is None:
                raise ValueError("ConversationBufferWindowMemory non disponibile (modulo langchain.memory mancante).")
        elif memory_type == "summary_buffer":
            if ConversationSummaryBufferMemory is None:
                raise ValueError("ConversationSummaryBufferMemory non disponibile (modulo langchain.memory mancante).")
            if llm is None:
                raise ValueError("Per 'summary_buffer' devi passare un LLM (parametro llm=...).")
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

        chat_history = self.get_session_history(session_id)

        if memory_type == "buffer_window":
            memory = ConversationBufferWindowMemory(
                k=max(1, settings.max_tokens // 100),
                return_messages=True,
                memory_key="chat_history",
                chat_memory=chat_history,
            )
        else:  # summary_buffer
            memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=max(128, settings.max_tokens // 2),
                return_messages=True,
                memory_key="chat_history",
                chat_memory=chat_history,
            )

        self.memory_configs[session_id] = {
            "type": memory_type,
            "created_at": datetime.now().isoformat(),
        }
        # refresh timeout
        self.session_timeouts[session_id] = datetime.now() + self.default_timeout
        return memory