"""
extractors.py — Estrazione testo da PDF (locale con PyMuPDF) o via OCR.space (REST)
-----------------------------------------------------------------------------------
Espone due funzioni principali:

- extract_text_and_blocks(pdf_bytes) -> tuple[str, list[dict]]
    Estrae il testo nativo del PDF e una lista di blocchi (layout-aware)
    usando PyMuPDF: per ogni blocco fornisce bounding box e testo.
    I blocchi sono utili al parser per euristiche su heading, nome/cognome, ecc.

- ocrspace_extract_text(pdf_bytes, language="ita") -> str
    Esegue OCR via OCR.space senza dipendenze esterne (solo stdlib).
    Usa la chiave pubblica "helloworld" (rate limitato): va bene per test.

Entrambe sono defensive (try/except) e sollevano eccezioni con messaggi chiari
che il layer FastAPI trasformerà in HTTP 4xx/5xx.
"""

from __future__ import annotations

import io
import json
import uuid
import urllib.request
from typing import List, Dict, Tuple

# Proviamo a importare PyMuPDF (pymupdf). Se non c'è, l'utente può installarlo da requirements.txt
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except Exception:
    fitz = None  # type: ignore
    HAS_PYMUPDF = False


# ===============================
# Estrazione locale (PyMuPDF)
# ===============================

def extract_text_and_blocks(pdf_bytes: bytes) -> Tuple[str, List[Dict]]:
    """
    Estrae:
      - text: l'intero testo del PDF (join delle pagine).
      - blocks: lista di blocchi con info layout per TUTTE le pagine.
        Ogni blocco: {
            "page": int,
            "x0": float, "y0": float, "x1": float, "y1": float,
            "text": str
        }

    Richiede PyMuPDF. Se non installato, solleva RuntimeError esplicativa.
    """
    if not HAS_PYMUPDF or fitz is None:
        raise RuntimeError("PyMuPDF non disponibile. Installa 'pymupdf' nel venv.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise RuntimeError(f"Impossibile aprire il PDF: {e}")

    all_text_parts: List[str] = []
    all_blocks: List[Dict] = []

    try:
        for pno in range(len(doc)):
            page = doc[pno]

            # Testo “semplice” della pagina
            page_text = page.get_text("text")
            if page_text:
                all_text_parts.append(page_text)

            # Blocchi layout-aware: "blocks" restituisce [(x0,y0,x1,y1,_,text,_,_)]
            # Per robustezza gestiamo eventuali campi mancanti.
            try:
                blocks = page.get_text("blocks") or []
            except Exception:
                blocks = []

            for b in blocks:
                # PyMuPDF può restituire tuple di lunghezza variabile a seconda della versione
                # La forma classica è: (x0, y0, x1, y1, "text", block_no, block_type, ...)
                x0 = float(b[0]) if len(b) > 0 else 0.0
                y0 = float(b[1]) if len(b) > 1 else 0.0
                x1 = float(b[2]) if len(b) > 2 else 0.0
                y1 = float(b[3]) if len(b) > 3 else 0.0
                text = str(b[4]) if len(b) > 4 and isinstance(b[4], str) else ""

                if text.strip():
                    all_blocks.append({
                        "page": pno,
                        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "text": text.strip()
                    })
    finally:
        doc.close()

    full_text = "\n".join(all_text_parts)
    return full_text, all_blocks


# ===============================
# Estrazione esterna (OCR.space)
# ===============================

_OCRSPACE_ENDPOINT = "https://api.ocr.space/parse/image"
# Nota: chiave pubblica per test. Ha limiti severi.
_OCRSPACE_APIKEY = "helloworld"


def ocrspace_extract_text(pdf_bytes: bytes, language: str = "ita") -> str:
    """
    Esegue OCR sul PDF via OCR.space.
    - Nessuna libreria extra (usa urllib della stdlib)
    - 'language' accetta codici come 'ita', 'eng', 'spa', ecc.

    Ritorna il testo concatenato (ParsedText dei risultati).
    Se l’OCR fallisce o è vuoto, ritorna stringa vuota: il chiamante decide come gestire.
    """
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = io.BytesIO()

    def _w(s: str) -> None:
        body.write(s.encode("utf-8"))

    # Campo lingua
    _w(f"--{boundary}\r\n")
    _w('Content-Disposition: form-data; name="language"\r\n\r\n')
    _w(f"{language}\r\n")

    # Un PDF può contenere tabelle. Non lo forziamo, lasciamo default "false".
    _w(f"--{boundary}\r\n")
    _w('Content-Disposition: form-data; name="isTable"\r\n\r\n')
    _w("false\r\n")

    # Allegato file
    _w(f"--{boundary}\r\n")
    _w('Content-Disposition: form-data; name="file"; filename="cv.pdf"\r\n')
    _w("Content-Type: application/pdf\r\n\r\n")
    body.write(pdf_bytes)
    _w("\r\n")
    _w(f"--{boundary}--\r\n")

    data = body.getvalue()

    req = urllib.request.Request(_OCRSPACE_ENDPOINT, data=data, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("apikey", _OCRSPACE_APIKEY)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

    try:
        payload = json.loads(raw)
    except Exception:
        return ""

    results = payload.get("ParsedResults") or []
    if not results:
        return ""

    # Concateno tutti i “ParsedText” (in PDF multipagina OCR.space restituisce più risultati)
    texts = []
    for r in results:
        pt = (r or {}).get("ParsedText") or ""
        if pt.strip():
            texts.append(pt)
    return "\n".join(texts).strip()
