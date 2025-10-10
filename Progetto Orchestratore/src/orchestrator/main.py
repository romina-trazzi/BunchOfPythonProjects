from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models.response import ExtractRequest, ExtractResponse
from .orchestrate import run_pipeline

from .utils.logger import logger as _app_logger  # side-effect: configura sink su file


app = FastAPI(
    title="Orchestratore Agent API",
    version="0.1.0",
    description="API per orchestrare Researcher, Critic e Writer.",
)

# ---- CORS (frontend React) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Endpoints di servizio ----
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Orchestratore Agent API. Vai su /docs per Swagger."}

# ---- Endpoint principale ----
@app.post("/extract_jobs", response_model=ExtractResponse)
def extract_jobs(payload: ExtractRequest) -> ExtractResponse:
    """
    Lancia la pipeline:
      - Researcher -> trova offerte
      - Critic     -> pulisce/valida
      - Writer     -> salva report + JSON/CSV in outputs/
    Ritorna il riepilogo strutturato (ExtractResponse).
    """
    return run_pipeline(job_title=payload.job_title, city=payload.city)