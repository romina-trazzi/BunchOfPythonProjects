# src/api/health.py
# -----------------
# Purpose:
#   Minimal health endpoints grouped under the "health" tag for Swagger.
#   Keep this file dependency-free so the app can always boot.
#
# Exposes:
#   GET /health  -> simple OK status for readiness/liveness probes
#   GET /ping    -> quick echo endpoint useful during troubleshooting
#
# How it's wired:
#   In src/app.py we "try_include_router('src.api.health')".
#   Once this module exists inside the image, FastAPI will include it.
#
# Notes:
#   - Return shapes are intentionally simple (dicts) to avoid pydantic coupling.
#   - If you need more details (version, uptime, env), extend the payload here.

from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check (liveness/readiness)")
def health() -> Dict[str, str]:
    """
    Return a minimal OK status that can be used by Docker/Kubernetes probes.
    """
    return {"status": "ok"}


@router.get("/ping", summary="Basic connectivity test")
def ping() -> Dict[str, str]:
    """
    Simple echo endpoint for quick manual testing or scripted checks.
    """
    return {"message": "pong"}
