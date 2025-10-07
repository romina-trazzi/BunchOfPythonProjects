"""
Vector store module per la Knowledge Base (Chroma + HuggingFaceEmbeddings)

COS'È:
    Un wrapper semplice attorno a Chroma che si occupa di:
      - inizializzare/persistire la collezione
      - aggiungere documenti (chunk)
      - cercare per similarità (con/senza punteggio)
      - pulire/eliminare la collezione
      - fornire un retriever LangChain

COSA FA:
    Espone la classe `VectorStoreManager` con metodi:
      - initialize_vector_store(collection_name: str = "rag_documents")
      - add_documents(documents)
      - similarity_search(query, k=..., filter_dict=...)
      - similarity_search_with_score(query, k=..., filter_dict=...)
      - get_retriever(search_kwargs: dict | None)
      - get_collection_info()
      - clear_collection()        -> cancella TUTTI i documenti (senza droppare la collezione)
      - delete_collection()       -> droppa la collezione dal disco
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Document LangChain
from langchain.schema import Document

# Chroma + Embeddings (namespace "community" per LangChain 0.2.x)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Config del progetto (directory, nome modello, top_k, ecc.)
from .config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    COS'È:
        Gestore del Vector Store (Chroma) con embeddings HuggingFace.
    NOTE:
        - Usa persistenza su disco (settings.chroma_persist_directory).
        - Di default il device è 'cpu'. Se usi GPU, puoi parametrizzarlo qui.
    """

    def __init__(self) -> None:
        # Embeddings HF: 'all-MiniLM-L6-v2' è veloce/leggero e compatibile.
        # normalize_embeddings=True migliora la similarità coseno con Chroma.
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embeddings_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vector_store: Optional[Chroma] = None
        self._ensure_persist_directory()

    # --------------------------------------------------------------------- #
    # INIT / PERSISTENZA
    # --------------------------------------------------------------------- #
    def _ensure_persist_directory(self) -> None:
        """Assicura che la directory di persistenza esista."""
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Chroma] Persist directory: {persist_dir.resolve()}")

    def initialize_vector_store(self, collection_name: str = "rag_documents") -> Chroma:
        """
        COSA FA:
            Crea o apre una collezione Chroma esistente con embeddings HF.
        RETURN:
            Oggetto `Chroma` pronto all'uso.
        """
        try:
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=settings.chroma_persist_directory,
            )
            logger.info(f"[Chroma] Initialized collection: {collection_name}")
            return self.vector_store
        except Exception as e:
            logger.error(f"[Chroma] Error initializing vector store: {e}")
            raise

    # --------------------------------------------------------------------- #
    # ADD DOCUMENTS
    # --------------------------------------------------------------------- #
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        COSA FA:
            Aggiunge una lista di Document (chunk) alla collezione.
        RETURN:
            Lista di ID assegnati da Chroma (se disponibili).
        """
        if not self.vector_store:
            self.initialize_vector_store()

        # Filtra documenti vuoti per evitare index error
        valid_docs = [d for d in documents if d and d.page_content and d.page_content.strip()]
        if not valid_docs:
            logger.warning("[Chroma] No valid documents to add")
            return []

        try:
            ids = self.vector_store.add_documents(valid_docs)
            # Persist sul disco (obbligatoria per rendere duraturi i cambi)
            self.vector_store.persist()
            logger.info(f"[Chroma] Added {len(valid_docs)} docs (persisted)")
            return ids or []
        except Exception as e:
            logger.error(f"[Chroma] Error adding documents: {e}")
            raise

    # --------------------------------------------------------------------- #
    # SEARCH
    # --------------------------------------------------------------------- #
    def similarity_search(
        self,
        query: str,
        k: Optional[int] = None,
        filter_dict: Optional[dict] = None,
    ) -> List[Document]:
        """
        COSA FA:
            Esegue una ricerca per similarità e ritorna i Document (senza punteggio).
        """
        if not self.vector_store:
            self.initialize_vector_store()
        k = k or settings.top_k_results

        try:
            results = self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
            logger.info(f"[Chroma] similarity_search -> {len(results)} hits")
            return results
        except Exception as e:
            logger.error(f"[Chroma] Error in similarity_search: {e}")
            raise

    def similarity_search_with_score(
        self,
        query: str,
        k: Optional[int] = None,
        filter_dict: Optional[dict] = None,
    ) -> List[Tuple[Document, float]]:
        """
        COSA FA:
            Esegue una ricerca per similarità e ritorna (Document, score).
            N.B.: lo score è tipicamente la distanza; minore è migliore.
        """
        if not self.vector_store:
            self.initialize_vector_store()
        k = k or settings.top_k_results

        try:
            results = self.vector_store.similarity_search_with_score(query=query, k=k, filter=filter_dict)
            logger.info(f"[Chroma] similarity_search_with_score -> {len(results)} hits")
            return results
        except Exception as e:
            logger.error(f"[Chroma] Error in similarity_search_with_score: {e}")
            raise

    # --------------------------------------------------------------------- #
    # RETRIEVER (per LC chains/agents)
    # --------------------------------------------------------------------- #
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        COSA FA:
            Ritorna un retriever LangChain wrapper attorno a Chroma.
            Utile se in futuro usi catene LCEL/agent che si aspettano .as_retriever().
        """
        if not self.vector_store:
            self.initialize_vector_store()
        if search_kwargs is None:
            search_kwargs = {"k": settings.top_k_results}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    # --------------------------------------------------------------------- #
    # INFO / MANUTENZIONE
    # --------------------------------------------------------------------- #
    def get_collection_info(self) -> dict:
        """
        COSA FA:
            Raccoglie informazioni base sulla collezione corrente:
              - name, count, embedding_model, persist_directory
        """
        if not self.vector_store:
            self.initialize_vector_store()
        try:
            # Accesso "interno" alla collezione per ottenere count()
            collection = self.vector_store._collection  # type: ignore[attr-defined]
            count = collection.count()
            return {
                "name": collection.name,
                "count": count,
                "embedding_model": settings.embeddings_model,
                "persist_directory": settings.chroma_persist_directory,
            }
        except Exception as e:
            logger.error(f"[Chroma] Error getting collection info: {e}")
            return {
                "name": None,
                "count": 0,
                "embedding_model": settings.embeddings_model,
                "persist_directory": settings.chroma_persist_directory,
                "error": str(e),
            }

    def clear_collection(self) -> dict:
        """
        COSA FA:
            Cancella TUTTI i documenti dalla collezione (senza dropparla).
            Utile per "svuotare" la KB mantenendo settaggi/metadata della collection.
        RETURN:
            { success: bool, message: str, deleted: int }
        """
        if not self.vector_store:
            self.initialize_vector_store()
        try:
            collection = self.vector_store._collection  # type: ignore[attr-defined]
            data = collection.get()
            ids = data.get("ids", []) if isinstance(data, dict) else []
            deleted = 0
            if ids:
                collection.delete(ids=ids)
                self.vector_store.persist()
                deleted = len(ids)
            msg = f"Cleared {deleted} document(s) from collection"
            logger.info(f"[Chroma] {msg}")
            return {"success": True, "message": msg, "deleted": deleted}
        except Exception as e:
            logger.error(f"[Chroma] Error clearing collection: {e}")
            return {"success": False, "message": str(e), "deleted": 0}

    def delete_collection(self) -> dict:
        """
        COSA FA:
            DROPPa la collezione (metadati inclusi). Dopo questa chiamata,
            la successiva initialize_vector_store ricreerà una collezione vuota.
        RETURN:
            { success: bool, message: str }
        """
        if not self.vector_store:
            # se non è inizializzato, proviamo comunque a creare e droppare
            self.initialize_vector_store()
        try:
            self.vector_store.delete_collection()
            logger.info("[Chroma] Collection dropped")
            return {"success": True, "message": "Collection dropped"}
        except Exception as e:
            logger.error(f"[Chroma] Error deleting collection: {e}")
            return {"success": False, "message": str(e)}