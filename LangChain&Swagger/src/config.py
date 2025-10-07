"""
Configuration module

COS'È:
    Un unico punto di verità per tutte le impostazioni dell'app:
    - chiavi API (es. Anthropic)
    - modelli embedding e persistenza Chroma
    - flag funzionali (agenti, memoria, web search, ecc.)
    - parametri di RAG (k, chunking)
    - logging e setup server

COSA FA:
    - Carica variabili d'ambiente (anche da .env)
    - Espone un'istanza globale `settings` per il resto del codice
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carica .env se presente (senza sollevare errore se manca)
load_dotenv()


class Settings(BaseSettings):
    """
    Classe di configurazione (Pydantic Settings)

    NOTE:
    - Ogni campo può essere sovrascritto da variabili d'ambiente.
    - Il file .env è letto automaticamente grazie a `model_config`.
    """

    # ------------------------ LLM provider (Anthropic) --------------------- #
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Chiave API Anthropic", validation_alias="ANTHROPIC_API_KEY"
    )
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Nome modello Anthropic (Claude)",
        validation_alias="ANTHROPIC_MODEL",
    )

    # ------------------------ Vector DB / Embeddings ----------------------- #
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        description="Directory persistenza Chroma",
        validation_alias="CHROMA_PERSIST_DIRECTORY",
    )
    embeddings_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Modello sentence-transformers per embeddings",
        validation_alias="EMBEDDINGS_MODEL",
    )

    # ------------------------ API Server ---------------------------------- #
    api_host: str = Field(default="0.0.0.0", description="Host FastAPI", validation_alias="API_HOST")
    api_port: int = Field(default=8000, description="Porta FastAPI", validation_alias="API_PORT")
    api_reload: bool = Field(default=True, description="Hot-reload in sviluppo", validation_alias="API_RELOAD")

    # ------------------------ RAG / Retrieval params ---------------------- #
    chunk_size: int = Field(default=1000, description="Dimensione chunking documenti", validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, description="Overlap chunking", validation_alias="CHUNK_OVERLAP")
    top_k_results: int = Field(default=5, description="K di default nelle ricerche", validation_alias="TOP_K_RESULTS")
    temperature: float = Field(default=0.7, description="Creatività LLM", validation_alias="TEMPERATURE")
    max_tokens: int = Field(default=1000, description="Max token output LLM", validation_alias="MAX_TOKENS")

    # ------------------------ Logging ------------------------------------- #
    log_level: str = Field(default="INFO", description="Livello log", validation_alias="LOG_LEVEL")
    log_file: str = Field(default="./logs/rag_engine.log", description="File log", validation_alias="LOG_FILE")

    # ------------------------ Feature flags -------------------------------- #
    enable_agents: bool = Field(default=True, description="Abilita agenti", validation_alias="ENABLE_AGENTS")
    enable_memory: bool = Field(default=True, description="Abilita memoria conversazionale", validation_alias="ENABLE_MEMORY")
    enable_code_execution: bool = Field(
        default=False, description="Abilita Python REPL (pericoloso in prod)", validation_alias="ENABLE_CODE_EXECUTION"
    )
    enable_web_search: bool = Field(default=True, description="Abilita web search tool", validation_alias="ENABLE_WEB_SEARCH")

    # ------------------------ Sessioni ------------------------------------ #
    session_timeout_hours: int = Field(
        default=24, description="Timeout sessioni (ore)", validation_alias="SESSION_TIMEOUT_HOURS"
    )
    max_sessions: int = Field(default=100, description="Numero massimo sessioni", validation_alias="MAX_SESSIONS")

    # ------------------------ Agenti -------------------------------------- #
    agent_max_iterations: int = Field(
        default=5, description="Max iterazioni per agente", validation_alias="AGENT_MAX_ITERATIONS"
    )
    agent_verbose: bool = Field(default=True, description="Verbose agenti", validation_alias="AGENT_VERBOSE")

    # ------------------------ Config Pydantic Settings --------------------- #
    model_config = SettingsConfigDict(
        env_file=".env",          # legge variabili anche da .env
        env_file_encoding="utf-8",
        case_sensitive=False,     # ENV_CASE insensitive
        extra="ignore",           # ignora variabili non mappate
    )


# Istanza globale importabile (es. from .config import settings)
settings = Settings()

# Crea cartelle di default se mancano (utile su Windows)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
os.makedirs(settings.chroma_persist_directory, exist_ok=True)
os.makedirs("./data/sessions", exist_ok=True)