"""
main.py — FastAPI minimale: /parse
Collega extractors → parsers → normalizers → scoring.
"""

from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from extractors import extract_text_and_blocks, ocrspace_extract_text, HAS_PYMUPDF
from parsers import parse_text_to_internal
from normalizers import to_schema
from scoring import completion

app = FastAPI(title="CV → JSON (backend)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # per sviluppo; chiudi in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Completion-Core", "X-Completion-Global"], # per scoring
)

@app.post("/parse")
async def parse(file: UploadFile = File(...), mode: str = "local", language: str = "eng"):
    """
    mode = 'local'   → PyMuPDF (testo nativo, più preciso se il PDF non è scansionato)
    mode = 'external'→ OCR.space (stdlib, chiave di test; più lento/limitato)
    language: 'eng' default (OCR) — usa 'ita','spa','fra', ecc. se ti serve
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Carica un PDF (Content-Type: application/pdf).")

    pdf_bytes = await file.read()
    filename = file.filename or "cv.pdf"

    # 1) estrazione testo (+ blocchi per layout-aware quando locale)
    if mode == "external":
        text = ocrspace_extract_text(pdf_bytes, language=language)
        if not text.strip():
            raise HTTPException(status_code=502, detail="OCR esterno non ha restituito testo (rate-limit o PDF non leggibile).")
        blocks = None
    else:
        if not HAS_PYMUPDF:
            raise HTTPException(status_code=500, detail="PyMuPDF non disponibile. Installa 'pymupdf' nel venv.")
        try:
            text, blocks = extract_text_and_blocks(pdf_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Estrazione locale fallita: {e}")

    # 2) parsing
    internal = parse_text_to_internal(text, blocks, filename)

    # 3) normalizzazione
    schema = to_schema(internal)

    # 4) scoring (TOP-LEVEL, NON dentro schema)
    from scoring import scores
    sc = scores(schema)

    return JSONResponse(
    content={"schema": schema}, 
    headers={
        "X-Completion-Core": str(sc["completezza_core_pct"]),
        "X-Completion-Global": str(sc["completezza_globale_pct"]),
    },
)