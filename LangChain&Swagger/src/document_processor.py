"""
Document processing module (loader + splitter)

COS'È:
    Un modulo di utilità che carica documenti (PDF/TXT/DOCX),
    li spezza in chunk uniformi e annota metadati utili
    prima dell'indicizzazione nel vector store.

COSA FA:
    - load_document(file_path): carica un singolo file come lista di Document
    - load_directory(directory_path): carica ricorsivamente tutti i file supportati
    - split_documents(documents): applica lo splitter (chunk_size/overlap da settings)
    - process_documents(source_path, is_directory=False): pipeline completa (load → split → tag)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

# LangChain types
from langchain.schema import Document

# Loader "nuovi" (namespace community per LC 0.2.x)
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    DirectoryLoader,
)

# Splitter "nuovo" (pacchetto separato)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    COS'È:
        Una classe stateless che incapsula il caricamento e lo splitting di documenti.

    NOTE:
        - Usa i parametri di chunking da settings (chunk_size/chunk_overlap).
        - Ritorna oggetti `Document` di LangChain pronti per il vector store.
    """

    def __init__(self) -> None:
        # Inizializza lo splitter con i parametri da configurazione
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],  # euristico robusto
        )

    # --------------------------------------------------------------------- #
    # LOADERS
    # --------------------------------------------------------------------- #
    def load_document(self, file_path: str | Path) -> List[Document]:
        """
        Carica un singolo file in una lista di `Document` (una pagina/segmento per elemento).

        Supporta:
            - .pdf  -> PyPDFLoader
            - .txt  -> TextLoader
            - .docx/.doc -> Docx2txtLoader
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(str(path))
            elif ext == ".txt":
                loader = TextLoader(str(path), encoding="utf-8")
            elif ext in (".docx", ".doc"):
                loader = Docx2txtLoader(str(path))
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            docs = loader.load()
            logger.info(f"[DP] Loaded {len(docs)} docs from {path.name}")
            return docs
        except Exception as e:
            logger.error(f"[DP] Error loading {path}: {e}")
            raise

    def load_directory(self, directory_path: str | Path, glob_pattern: str = "**/*") -> List[Document]:
        """
        Carica ricorsivamente tutti i file supportati da una directory.

        Per ogni estensione supportata, usa un DirectoryLoader dedicato.
        """
        dpath = Path(directory_path)
        if not dpath.exists() or not dpath.is_dir():
            raise FileNotFoundError(f"Directory not found: {dpath}")

        mapping = {
            ".pdf": (PyPDFLoader, {}),
            ".txt": (TextLoader, {"encoding": "utf-8"}),
            ".docx": (Docx2txtLoader, {}),
            ".doc": (Docx2txtLoader, {}),
        }

        all_docs: List[Document] = []
        for ext, (loader_cls, kwargs) in mapping.items():
            try:
                loader = DirectoryLoader(
                    str(dpath),
                    glob=f"**/*{ext}",
                    loader_cls=loader_cls,
                    loader_kwargs=kwargs,
                )
                docs = loader.load()
                logger.info(f"[DP] Loaded {len(docs)} {ext} docs from {dpath}")
                all_docs.extend(docs)
            except Exception as e:
                # Non blocchiamo l'intero batch: log e continuiamo con le altre estensioni
                logger.warning(f"[DP] Error loading {ext} in {dpath}: {e}")

        logger.info(f"[DP] Total documents loaded: {len(all_docs)}")
        return all_docs

    # --------------------------------------------------------------------- #
    # SPLITTING
    # --------------------------------------------------------------------- #
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Applica lo splitter a una lista di Document e ritorna i chunk risultanti.
        """
        if not documents:
            return []
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"[DP] Split {len(documents)} docs into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"[DP] Error splitting documents: {e}")
            raise

    # --------------------------------------------------------------------- #
    # PIPELINE COMPLETA
    # --------------------------------------------------------------------- #
    def process_documents(self, source_path: str | Path, is_directory: bool = False) -> List[Document]:
        """
        Pipeline completa:
            - load (file o directory)
            - split
            - tagging metadati (chunk_id, source, source_path, chunk_size)
        """
        try:
            # 1) Caricamento
            if is_directory:
                docs = self.load_directory(source_path)
            else:
                docs = self.load_document(source_path)

            if not docs:
                logger.warning("[DP] No documents loaded")
                return []

            # 2) Splitting
            chunks = self.split_documents(docs)

            # 3) Metadati coerenti per l'indicizzazione
            src = str(Path(source_path))
            for i, c in enumerate(chunks):
                # Mantiene 'source' se già presente (es. PyPDFLoader), altrimenti usa il nome file/dir
                c.metadata.setdefault("source", c.metadata.get("source", Path(src).name))
                c.metadata.update(
                    {
                        "chunk_id": i,
                        "source_path": src,
                        "chunk_size": len(c.page_content),
                    }
                )

            return chunks
        except Exception as e:
            logger.error(f"[DP] Error processing documents from {source_path}: {e}")
            raise