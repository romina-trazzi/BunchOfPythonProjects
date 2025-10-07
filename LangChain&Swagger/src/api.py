"""
FastAPI REST API (no rag_engine)

COS'È:
    Il front-end HTTP della tua app RAG/Agents, SENZA dipendenze da rag_engine.py.
    Inizializza e usa direttamente:
      - VectorStoreManager (Chroma + HF embeddings)
      - MemoryManager (sessions/history su file)
      - [opzionale] LLM Anthropic Claude (se hai la chiave)
      - RAGAgentManager (agenti LangChain)

COSA FA:
    - Upload & indicizzazione documenti (file e directory)
    - Similarity search (con/ senza score)
    - Info/clear collection
    - Agenti (conversation, research, analysis, [coding se abilitato])
    - Sessioni (lista, history, delete)
    - Query “semplice”: retrieval-only o con LLM se presente
    - Swagger UI custom su /docs
"""

from __future__ import annotations

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

# LangChain LLM (opzionale)
try:
    from langchain_anthropic import ChatAnthropic
except Exception:
    ChatAnthropic = None  # consente di avviare l'API anche senza pacchetto

# Loader & splitter “nuovi” (LangChain 0.2.x)
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Moduli del progetto
from .config import settings
from .vector_store import VectorStoreManager
from .memory_manager import MemoryManager
from .agents import RAGAgentManager
from .swagger_config import (
    tags_metadata,
    swagger_ui_custom_css,
    swagger_ui_custom_js,
)
from .models import (
    # health/error
    HealthResponse,
    ErrorResponse,
    # upload/collection/clear
    DocumentUploadResponse,
    CollectionInfoResponse,
    ClearDocumentsResponse,
    CollectionInfo,
    # similarity
    SimilarDocumentsRequest,
    SimilarDocumentsResponse,
    SimilarDocument,
    # query semplice
    QueryRequest,
    QueryResponse,
    SourceDocument,
    # agenti
    AgentQueryRequest,
    AgentQueryResponse,
    AgentListResponse,
    AgentListItem,
    # sessioni
    SessionListResponse,
    SessionDeleteResponse,
    ConversationHistoryResponse,
    ConversationHistoryItem,
)

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# APP
# -----------------------------------------------------------------------------
app = FastAPI(
    title="🤖 RAG + Agents API (no rag_engine)",
    description="""
    Backend minimale per RAG + Agents, senza dipendere da rag_engine.py.

    **Componenti**
    - VectorStoreManager (Chroma + HuggingFaceEmbeddings)
    - MemoryManager (sessioni su file)
    - [opzionale] LLM Anthropic Claude
    - RAGAgentManager (agenti LangChain)

    **Funzionalità**
    - Upload (file/directory) + indicizzazione
    - Similarity search
    - Info/clear collection
    - Agenti (conversation, research, analysis, [coding])
    - Sessioni (list/delete/history)
    - Query semplice (retrieval-only o con LLM se configurato)
    """,
    version="2.1.0",
    docs_url=None,  # serviamo una UI custom su /docs
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
)

# CORS aperto (regola in produzione)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# STATO GLOBALE (componenti)
# -----------------------------------------------------------------------------
app_start_time = time.time()
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# componenti inizializzati nello startup
VSM: Optional[VectorStoreManager] = None
MEM: Optional[MemoryManager] = None
LLM = None
AGENTS: Optional[RAGAgentManager] = None


# -----------------------------------------------------------------------------
# HELPER: LLM opzionale
# -----------------------------------------------------------------------------
def _build_llm():
    """
    COSA FA:
        Crea un'istanza di ChatAnthropic se possibile (chiave + pacchetto).
        Ritorna None se non configurato (l'API funziona comunque).
    """
    if not settings.enable_agents:
        return None
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY mancante: agenti abilitati ma LLM non configurato.")
        return None
    if ChatAnthropic is None:
        logger.warning("langchain-anthropic non installato: impossibile creare ChatAnthropic.")
        return None

    return ChatAnthropic(
        anthropic_api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


# -----------------------------------------------------------------------------
# HELPER: caricamento + split documenti
# -----------------------------------------------------------------------------
def _make_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap, length_function=len
    )


def _load_single_file(file_path: Path) -> List[Document]:
    """
    COSA FA:
        Carica un singolo file nei Document di LangChain (una pagina/segmento = Document).
    """
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif ext == ".txt":
        loader = TextLoader(str(file_path), encoding="utf-8")
    elif ext in (".docx", ".doc"):
        loader = Docx2txtLoader(str(file_path))
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    docs = loader.load()
    logger.info(f"Loaded {len(docs)} docs from {file_path.name}")
    return docs


def _load_directory(dir_path: Path) -> List[Document]:
    """
    COSA FA:
        Carica TUTTI i file supportati nella directory (ricorsivo).
    """
    all_docs: List[Document] = []
    mapping = {
        ".pdf": (PyPDFLoader, {}),
        ".txt": (TextLoader, {"encoding": "utf-8"}),
        ".docx": (Docx2txtLoader, {}),
        ".doc": (Docx2txtLoader, {}),
    }
    for ext, (loader_cls, kwargs) in mapping.items():
        loader = DirectoryLoader(str(dir_path), glob=f"**/*{ext}", loader_cls=loader_cls, loader_kwargs=kwargs)
        docs = loader.load()
        logger.info(f"Loaded {len(docs)} {ext} docs from directory")
        all_docs.extend(docs)
    return all_docs


def _split_and_tag(docs: List[Document], source_path: str) -> List[Document]:
    """
    COSA FA:
        Splitta i Document in chunk e aggiunge metadati coerenti.
    """
    splitter = _make_splitter()
    chunks = splitter.split_documents(docs)
    for i, c in enumerate(chunks):
        c.metadata.update(
            {
                "chunk_id": i,
                "source": c.metadata.get("source", Path(source_path).name),
                "source_path": source_path,
                "chunk_size": len(c.page_content),
            }
        )
    return chunks


# -----------------------------------------------------------------------------
# STARTUP / SHUTDOWN
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    COSA FA:
        Inizializza VectorStoreManager, MemoryManager, (opzionale) LLM e AgentManager.
    """
    global VSM, MEM, LLM, AGENTS
    logger.info("Bootstrapping components...")
    VSM = VectorStoreManager()
    VSM.initialize_vector_store()
    MEM = MemoryManager()
    LLM = _build_llm()
    if settings.enable_agents and LLM is not None:
        AGENTS = RAGAgentManager(LLM, VSM, MEM)
        logger.info("Agent manager ready")
    else:
        AGENTS = None
        logger.info("Agents disabled or LLM not configured.")
    logger.info("Startup completed.")


# -----------------------------------------------------------------------------
# EXCEPTION HANDLER
# -----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", detail=str(exc), timestamp=datetime.now().isoformat()
        ).dict(),
    )


# -----------------------------------------------------------------------------
# DOCS CUSTOM
# -----------------------------------------------------------------------------
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>RAG+Agents Docs</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
        <style>{swagger_ui_custom_css}</style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script>
          window.onload = function() {{
            const ui = SwaggerUIBundle({{
              url: '/openapi.json',
              dom_id: '#swagger-ui',
              presets: [SwaggerUIBundle.presets.apis],
              layout: "BaseLayout"
            }});
            {swagger_ui_custom_js}
          }};
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    return JSONResponse(
        get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=app.description,
            tags=tags_metadata,
        )
    )


# -----------------------------------------------------------------------------
# HEALTH
# -----------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["🏥 Health"], summary="Health Check")
async def health_check():
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy", timestamp=datetime.now().isoformat(), version=app.version, uptime_seconds=uptime
    )


# -----------------------------------------------------------------------------
# UPLOAD & INDICIZZAZIONE
# -----------------------------------------------------------------------------
@app.post(
    "/upload/file",
    response_model=DocumentUploadResponse,
    tags=["📚 Document Management"],
    summary="Upload Single File",
)
async def upload_file(file: UploadFile = File(..., description="PDF, DOCX, TXT")):
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    allowed = {".pdf", ".txt", ".docx", ".doc"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}")

    temp_path = UPLOAD_DIR / file.filename
    try:
        # salva temporaneo
        data = await file.read()
        with open(temp_path, "wb") as f:
            f.write(data)

        # carica -> split -> tag
        docs = _load_single_file(temp_path)
        chunks = _split_and_tag(docs, str(temp_path))

        # indicizza
        ids = VSM.add_documents(chunks)

        return DocumentUploadResponse(
            success=True,
            message=f"Indexed {len(chunks)} chunks",
            documents_added=len(chunks),
            document_ids=ids,
            source_file=str(temp_path),
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # pulizia file temporaneo
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.post(
    "/upload/directory",
    response_model=DocumentUploadResponse,
    tags=["📚 Document Management"],
    summary="Upload Directory",
)
async def upload_directory(directory_path: str = Body(..., embed=True, description="Percorso directory")):
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    d = Path(directory_path)
    if not d.exists() or not d.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    try:
        docs = _load_directory(d)
        if not docs:
            return DocumentUploadResponse(
                success=False, message="No supported documents found", documents_added=0, source_directory=str(d)
            )
        chunks = _split_and_tag(docs, str(d))
        ids = VSM.add_documents(chunks)
        return DocumentUploadResponse(
            success=True,
            message=f"Indexed {len(chunks)} chunks from directory",
            documents_added=len(chunks),
            document_ids=ids,
            source_directory=str(d),
        )
    except Exception as e:
        logger.error(f"Directory upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# SIMILARITY / COLLECTION
# -----------------------------------------------------------------------------
@app.post(
    "/search/similar",
    response_model=SimilarDocumentsResponse,
    tags=["🔍 Search"],
    summary="Similar Documents",
)
async def search_similar_documents(request: SimilarDocumentsRequest):
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    try:
        pairs = VSM.similarity_search_with_score(query=request.query, k=request.k)
        docs = [
            SimilarDocument(
                content=doc.page_content,
                metadata=doc.metadata,
                similarity_score=float(score),
                source=doc.metadata.get("source", "Unknown"),
            )
            for doc, score in pairs
        ]
        return SimilarDocumentsResponse(success=True, query=request.query, documents=docs)
    except Exception as e:
        logger.error(f"Error searching similar docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/collection/info",
    response_model=CollectionInfoResponse,
    tags=["📚 Document Management"],
    summary="Collection Info",
)
async def get_collection_info():
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    try:
        info = VSM.get_collection_info()
        return CollectionInfoResponse(
            success=True,
            info=CollectionInfo(
                name=info.get("name"),
                count=info.get("count", 0),
                embedding_model=info.get("embedding_model", settings.embeddings_model),
                persist_directory=info.get("persist_directory", settings.chroma_persist_directory),
            ),
        )
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        return CollectionInfoResponse(success=False, message=str(e))


@app.delete(
    "/collection/clear",
    response_model=ClearDocumentsResponse,
    tags=["📚 Document Management"],
    summary="Clear Collection",
)
async def clear_collection():
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    try:
        result = VSM.clear_collection()
        return ClearDocumentsResponse(**result)  # {success,message,deleted}
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# QUERY "SEMPLICE" (retrieval-only o con LLM se presente)
# -----------------------------------------------------------------------------
@app.post("/query", response_model=QueryResponse, tags=["🔍 RAG Queries"], summary="Simple Query")
async def simple_query(request: QueryRequest):
    """
    COSA FA:
        - Recupera i top-k chunk dalla KB
        - Se LLM configurato: produce una risposta breve usando i chunk come contesto
        - Altrimenti: ritorna solo le sorgenti + messaggio esplicativo
    """
    if VSM is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")

    start = time.time()
    k = request.k or settings.top_k_results
    try:
        docs = VSM.similarity_search(request.question, k=k)
        sources = [
            SourceDocument(
                content=d.page_content,
                metadata=d.metadata,
                source=d.metadata.get("source", "Unknown"),
            )
            for d in docs
        ]

        answer = None
        note = None

        if LLM is not None:
            # prompt minimale e sicuro (no hallucination claims)
            context = "\n\n".join([f"- {d.page_content[:800]}" for d in docs])
            prompt = (
                "Rispondi brevemente alla domanda usando SOLO il contesto:\n\n"
                f"Contesto:\n{context}\n\n"
                f"Domanda: {request.question}\n\n"
                "Se la risposta non è presente nel contesto, dì 'Non lo so'."
            )
            ans = LLM.invoke(prompt)
            # LLM.invoke ritorna un AIMessage; estrai il testo
            answer = getattr(ans, "content", None) or str(ans)
        else:
            note = (
                "LLM non configurato: ritorno solo i documenti più simili. "
                "Imposta ANTHROPIC_API_KEY per abilitare la risposta generata."
            )

        elapsed = time.time() - start
        return QueryResponse(
            success=True,
            question=request.question,
            answer=answer,
            response_time_seconds=elapsed,
            timestamp=datetime.now().isoformat(),
            sources=sources if request.include_sources else None,
            num_sources=len(sources) if request.include_sources else None,
            message=note,
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# AGENTI
# -----------------------------------------------------------------------------
@app.get("/agents", response_model=AgentListResponse, tags=["🤖 AI Agents"], summary="List available agents")
async def list_agents():
    if not settings.enable_agents:
        return AgentListResponse(success=True, agents=[])
    if AGENTS is None:
        return AgentListResponse(success=True, agents=[])
    items = [
        AgentListItem(name=a["name"], description=a["description"])
        for a in AGENTS.list_available_agents()
    ]
    return AgentListResponse(success=True, agents=items)


@app.post(
    "/agent/query",
    response_model=AgentQueryResponse,
    tags=["🤖 AI Agents"],
    summary="Query with AI Agent",
)
async def agent_query(request: AgentQueryRequest):
    if not settings.enable_agents or AGENTS is None:
        raise HTTPException(status_code=503, detail="Agents unavailable (LLM not configured or disabled).")
    try:
        result = AGENTS.execute_agent(request.agent_type, request.query, session_id=request.session_id)
        return AgentQueryResponse(
            answer=result["output"],
            agent_type=request.agent_type,
            agent_steps=result.get("actions_taken", []),
            session_id=result["session_id"],
            timestamp=result["timestamp"],
        )
    except Exception as e:
        logger.error(f"Agent query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# SESSIONI
# -----------------------------------------------------------------------------
@app.get("/sessions", response_model=SessionListResponse, tags=["💬 Session Management"], summary="List sessions")
async def get_sessions():
    if MEM is None:
        raise HTTPException(status_code=503, detail="Memory manager not ready")
    sessions = MEM.get_all_sessions()
    return SessionListResponse(success=True, sessions=sessions, session_count=len(sessions))


@app.delete(
    "/sessions/{session_id}",
    response_model=SessionDeleteResponse,
    tags=["💬 Session Management"],
    summary="Delete session",
)
async def delete_session(session_id: str):
    if MEM is None:
        raise HTTPException(status_code=503, detail="Memory manager not ready")
    ok = MEM.clear_session(session_id)
    return SessionDeleteResponse(
        success=ok, message=("Session cleared" if ok else "Failed to clear session"), session_id=session_id
    )


@app.get(
    "/sessions/{session_id}/history",
    response_model=ConversationHistoryResponse,
    tags=["💬 Session Management"],
    summary="Get conversation history",
)
async def get_conversation_history(session_id: str):
    if MEM is None:
        raise HTTPException(status_code=503, detail="Memory manager not ready")
    hist = MEM.get_session_history(session_id).messages
    items = [
        ConversationHistoryItem(
            type=("human" if m.type == "human" or m.__class__.__name__ == "HumanMessage" else "ai"),
            content=m.content,
        )
        for m in hist
    ]
    return ConversationHistoryResponse(
        success=True, history=items, session_id=session_id, message_count=len(items)
    )


@app.delete(
    "/sessions/{session_id}/history",
    tags=["💬 Session Management"],
    summary="Clear conversation history",
)
async def clear_conversation_history(session_id: str):
    if MEM is None:
        raise HTTPException(status_code=503, detail="Memory manager not ready")
    MEM.get_session_history(session_id).clear()
    return {"success": True, "message": f"History cleared for session {session_id}"}


# -----------------------------------------------------------------------------
# STREAMING (placeholder)
# -----------------------------------------------------------------------------
@app.get("/stream", tags=["⚡ Streaming"], summary="Streaming Info")
async def stream_info():
    return {"message": "Streaming SSE non abilitato in questa build. Usa /query per ora."}


# -----------------------------------------------------------------------------
# ROOT
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "RAG + Agents API (no rag_engine)",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload_file": "POST /upload/file",
            "upload_directory": "POST /upload/directory",
            "search_similar": "POST /search/similar",
            "collection_info": "GET /collection/info",
            "collection_clear": "DELETE /collection/clear",
            "query_simple": "POST /query",
            "agents_list": "GET /agents",
            "agent_query": "POST /agent/query",
            "sessions": "GET /sessions",
        },
    }


# -----------------------------------------------------------------------------
# MAIN (sviluppo)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )