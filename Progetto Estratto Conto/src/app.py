# src/app.py
# ----------
# Entry point FastAPI per l'app Estratto Conto.
# - Espone rotte di health check e API ML (/v1/*)
# - Abilita CORS per sviluppo locale
# - Monta contenuti statici (frontend, se presenti)
# - Espone la documentazione su /api/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Tenta di importare il router ML
try:
    from src.api.predizioni import router as ml_router
except Exception as e:
    ml_router = None
    print(f"[WARN] Non riesco a importare src.api.predizioni: {e}")

# ------------------------------------------------------------
# Crea l'app FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title="Estratto Conto API",
    version="1.0.0",
    openapi_url="/api/openapi.json",  # Serve schema OpenAPI dietro proxy
    docs_url="/api/docs",             # Swagger UI
    swagger_ui_parameters={"docExpansion": "list"},
)

# ------------------------------------------------------------
# Middleware CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # per sviluppo locale; restringere in produzione
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Mount static (solo se la directory esiste)
# ------------------------------------------------------------
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    print("[INFO] Directory 'static' non trovata — salto il montaggio static.")

# ------------------------------------------------------------
# Rotte base
# ------------------------------------------------------------
@app.get("/")
def index():
    return {
        "name": "Estratto Conto API",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
        "health": "/health",
        "ml_endpoints": "/v1/*",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------
# Monta il router ML se disponibile
# ------------------------------------------------------------
if ml_router:
    app.include_router(ml_router)
    print("[INFO] Router ML /v1 montato correttamente.")
else:
    @app.get("/_router_missing")
    def router_missing():
        return {
            "error": "src.api.predizioni non trovato",
            "hint": "Crea src/api/predizioni.py e definisci router = APIRouter(prefix='/v1')",
        }

# ------------------------------------------------------------
# Main (per avvio diretto)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8081,  log_level="info")