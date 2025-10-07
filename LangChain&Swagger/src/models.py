"""
Pydantic models per API requests/responses

COS'È:
    La definizione tipata degli oggetti che l'API espone/accetta:
    - Health & error
    - Upload documenti / info collezione / clear
    - Similarity search (request/response)
    - Gestione sessioni (list/delete/history)
    - Agenti (request/response)

COSA FA:
    Valida e documenta automaticamente i payload FastAPI (OpenAPI/Swagger),
    garantendo formati coerenti tra client e server.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Health & Error
# =============================================================================
class HealthResponse(BaseModel):
    """Payload dello stato salute del servizio."""

    status: str = Field(..., description="healthy / degraded / down")
    timestamp: str = Field(..., description="ISO datetime della rilevazione")
    version: str = Field(..., description="Versione dell'app")
    uptime_seconds: Optional[float] = Field(None, description="Uptime in secondi")


class ErrorResponse(BaseModel):
    """Payload errore standardizzato usato dal global exception handler."""

    success: bool = Field(False, description="Sempre False per gli errori")
    error: str = Field(..., description="Titolo/chiave errore")
    detail: Optional[str] = Field(None, description="Dettaglio/stack semplificato")
    timestamp: str = Field(..., description="ISO datetime dell'errore")


# =============================================================================
# Query "semplice" (se mantieni un endpoint /query o per lo streaming SSE)
# =============================================================================
class QueryRequest(BaseModel):
    """
    Richiesta per una query 'semplice' (non-Agente).
    Può essere usata per endpoint come /query o /query/stream (SSE).
    """

    question: str = Field(..., min_length=1, description="Domanda naturale dell'utente")
    include_sources: bool = Field(True, description="Includere i documenti sorgente nella risposta")
    k: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Numero documenti da recuperare (override del default server)",
    )


class SourceDocument(BaseModel):
    """Singolo documento sorgente citato in risposta."""

    content: str = Field(..., description="Testo/chunk del documento")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati arbitrari (es. source, page, etc.)")
    source: str = Field(..., description="Nome o percorso origine (se disponibile)")


class QueryResponse(BaseModel):
    """Risposta per query 'semplice'."""

    success: bool = Field(..., description="True se l'elaborazione è riuscita")
    question: str = Field(..., description="Echo della domanda")
    answer: Optional[str] = Field(None, description="Risposta generata (se disponibile)")
    response_time_seconds: float = Field(..., description="Tempo di risposta lato server")
    timestamp: str = Field(..., description="ISO datetime della risposta")
    sources: Optional[List[SourceDocument]] = Field(None, description="Elenco documenti citati")
    num_sources: Optional[int] = Field(None, description="Numero di sorgenti incluse")
    message: Optional[str] = Field(None, description="Nota aggiuntiva (warning, fallback, ecc.)")


# =============================================================================
# Upload / Collection info / Clear
# =============================================================================
class DocumentUploadResponse(BaseModel):
    """Risposta per upload e indicizzazione di documenti."""

    success: bool = Field(..., description="True se l'upload/indicizzazione è andato a buon fine")
    message: str = Field(..., description="Messaggio di stato")
    documents_added: int = Field(..., ge=0, description="Numero di chunk/documenti indicizzati")
    document_ids: Optional[List[str]] = Field(None, description="IDs assegnati dal vector store (se disponibili)")
    processing_time_seconds: Optional[float] = Field(None, description="Tempo di processamento")
    source_file: Optional[str] = Field(None, description="Percorso file originale (per upload singolo)")
    source_directory: Optional[str] = Field(None, description="Directory di origine (per upload directory)")


class CollectionInfo(BaseModel):
    """Informazioni di base sulla collezione attiva nel vector store."""

    name: Optional[str] = Field(None, description="Nome collezione")
    count: int = Field(..., ge=0, description="Numero documenti/chunk indicizzati")
    embedding_model: str = Field(..., description="Modello embeddings in uso")
    persist_directory: str = Field(..., description="Percorso directory persistenza")


class CollectionInfoResponse(BaseModel):
    """Payload wrapper per info collezione."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    info: Optional[CollectionInfo] = Field(None, description="Informazioni collezione")
    message: Optional[str] = Field(None, description="Messaggio/errore (se failure)")


class ClearDocumentsResponse(BaseModel):
    """Risposta per lo svuotamento della collezione."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio di esito")
    deleted: Optional[int] = Field(None, ge=0, description="Numero documenti cancellati (se calcolato)")


# =============================================================================
# Similarity Search
# =============================================================================
class SimilarDocumentsRequest(BaseModel):
    """Richiesta per una ricerca di documenti simili senza generare risposta LLM."""

    query: str = Field(..., min_length=1, description="Query testuale per il retriever")
    k: int = Field(5, ge=1, le=50, description="Numero massimo di risultati")


class SimilarDocument(BaseModel):
    """Singolo documento simile con punteggio."""

    content: str = Field(..., description="Contenuto del chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati associati")
    similarity_score: float = Field(..., description="Score di similarità (dipende dal vector store)")
    source: str = Field(..., description="Fonte/etichetta del documento")


class SimilarDocumentsResponse(BaseModel):
    """Risposta per similarity search."""

    success: bool = Field(..., description="True se la ricerca è andata a buon fine")
    query: str = Field(..., description="Echo della query")
    documents: List[SimilarDocument] = Field(default_factory=list, description="Lista documenti simili")
    message: Optional[str] = Field(None, description="Messaggio/nota (se presente)")


# =============================================================================
# Agenti (LangChain Agents)
# =============================================================================
AgentType = Literal["conversation", "research", "analysis", "coding"]


class AgentQueryRequest(BaseModel):
    """Richiesta per eseguire un agente specializzato."""

    query: str = Field(..., min_length=1, description="Input naturale per l'agente")
    session_id: str = Field(default="default", description="Identificatore sessione conversazionale")
    agent_type: AgentType = Field(
        default="conversation",
        description="Tipo di agente da usare (conversation | research | analysis | coding)",
    )


class AgentQueryResponse(BaseModel):
    """Risposta di un agente con eventuali passi intermedi (tool calls)."""

    answer: str = Field(..., description="Output finale dell'agente")
    agent_type: AgentType = Field(..., description="Tipo di agente usato")
    agent_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Azioni/step compiuti dall'agente")
    session_id: str = Field(..., description="Sessione a cui appartiene l'interazione")
    timestamp: str = Field(..., description="ISO datetime della risposta")


class AgentListItem(BaseModel):
    """Elemento della lista agenti disponibili (nome + descrizione)."""

    name: AgentType = Field(..., description="Nome agente")
    description: str = Field(..., description="Breve descrizione")


class AgentListResponse(BaseModel):
    """Risposta per la lista degli agenti disponibili."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    agents: List[AgentListItem] = Field(default_factory=list, description="Elenco agenti")


# =============================================================================
# Sessioni (gestite da MemoryManager)
# =============================================================================
class SessionListResponse(BaseModel):
    """Elenco delle sessioni note al sistema (in RAM o su disco)."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    sessions: List[str] = Field(default_factory=list, description="Lista di session_id")
    session_count: int = Field(..., ge=0, description="Numero totale di sessioni")


class SessionDeleteResponse(BaseModel):
    """Esito della cancellazione di una sessione."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio di stato")
    session_id: str = Field(..., description="Sessione interessata")


class ConversationHistoryItem(BaseModel):
    """Singolo messaggio nella history conversazionale."""

    type: Literal["human", "ai"] = Field(..., description="Ruolo del messaggio")
    content: str = Field(..., description="Testo del messaggio")


class ConversationHistoryResponse(BaseModel):
    """History messaggi di una sessione."""

    success: bool = Field(..., description="True se l'operazione è riuscita")
    history: List[ConversationHistoryItem] = Field(default_factory=list, description="Messaggi (ordine cronologico)")
    session_id: str = Field(..., description="Identificatore della sessione")
    message_count: int = Field(..., ge=0, description="Numero di messaggi totali in history")