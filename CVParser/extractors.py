"""
extractors.py — Estrazione testo da PDF (locale con PyMuPDF) o via OCR.space (REST)
-----------------------------------------------------------------------------------
Espone due funzioni principali:

- extract_text_and_blocks(pdf_bytes) -> tuple[str, list[dict]]
    Estrae il testo nativo del PDF e una lista di blocchi (layout-aware)
    usando PyMuPDF. In questa versione ogni blocco rappresenta una *riga*,
    con bounding box e info tipografiche utili al parser:
      {
        "page": int,
        "x0": float, "y0": float, "x1": float, "y1": float,
        "text": str,
        "font_size": float,   # max size tra gli spans della riga
        "is_bold": bool,      # true se un font della riga è bold
        "line_no": int        # numero di riga crescente per pagina
      }

- ocrspace_extract_text(pdf_bytes, language="ita") -> str
    (Invariata) Esegue OCR via OCR.space senza dipendenze esterne (solo stdlib).
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
# Estrazione locale (PyMuPDF) — versione "layout-aware" arricchita
# ===============================

def extract_text_and_blocks(pdf_bytes: bytes) -> Tuple[str, List[Dict]]:
    """
    Estrae:
      - text: l'intero testo del PDF (join delle pagine).
      - blocks: lista di *righe* con info layout e tipografiche per TUTTE le pagine.
        Ogni blocco: {
            "page": int,
            "x0": float, "y0": float, "x1": float, "y1": float,
            "text": str,
            "font_size": float,
            "is_bold": bool,
            "line_no": int
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
            page_text = page.get_text("text") or ""
            if page_text:
                all_text_parts.append(page_text)

            # Ricostruzione linee con info di font/bold via get_text("dict")
            try:
                d = page.get_text("dict") or {}
            except Exception:
                d = {}

            line_no = 0
            for b in d.get("blocks", []):
                if "lines" not in b:
                    # es. blocchi immagine
                    continue
                for l in b.get("lines", []):
                    line_no += 1
                    spans = l.get("spans", []) or []
                    text_parts: List[str] = []
                    max_size: float = 0.0
                    is_bold: bool = False

                    for s in spans:
                        t = s.get("text") or ""
                        if t:
                            text_parts.append(t)
                        try:
                            size = float(s.get("size", 0.0) or 0.0)
                        except Exception:
                            size = 0.0
                        if size > max_size:
                            max_size = size
                        fname = (s.get("font") or "").lower()
                        if "bold" in fname or fname.endswith("b"):
                            is_bold = True

                    text = " ".join(text_parts).strip()
                    if not text:
                        continue

                    try:
                        x0, y0, x1, y1 = l.get("bbox", [0, 0, 0, 0])
                    except Exception:
                        x0 = y0 = x1 = y1 = 0.0

                    all_blocks.append({
                        "page": pno,
                        "x0": float(x0), "y0": float(y0),
                        "x1": float(x1), "y1": float(y1),
                        "text": text,
                        "font_size": float(max_size),
                        "is_bold": bool(is_bold),
                        "line_no": int(line_no),
                    })
    finally:
        doc.close()

    full_text = "\n".join(all_text_parts)
    return full_text, all_blocks


# ===============================
# Estrazione esterna (OCR.space) — INVARIATA
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

    texts = []
    for r in results:
        pt = (r or {}).get("ParsedText") or ""
        if pt.strip():
            texts.append(pt)
    return "\n".join(texts).strip()
