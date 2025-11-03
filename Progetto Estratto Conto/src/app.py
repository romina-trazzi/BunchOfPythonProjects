# src/app.py
# ----------
# FastAPI application entrypoint:
# - exposes index and health routes
# - enables permissive CORS for local dev
# - includes the ML router defined in src/api/predizioni.py
# - IMPORTANT: docs and openapi are under /api/* to work behind Nginx proxy

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try to load ML router (/v1/* endpoints). If missing, we still start the app.
try:
    from src.api.predizioni import router as ml_router
except Exception as e:
    ml_router = None
    print(f"[WARN] Could not import src.api.predizioni: {e}")

app = FastAPI(
    title="Estratto Conto API",
    version="1.0.0",
    openapi_url="/api/openapi.json",  # <â€” prefix with /api so Swagger fetches the right URL behind Nginx
    docs_url="/api/docs",             # <â€” serve Swagger UI under /api/docs
    swagger_ui_parameters={"docExpansion": "list"},
)

# CORS for local dev; OK because frontend is served by Nginx same-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # limit in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    # Keep these absolute URLs in sync with openapi/docs settings
    return {
        "name": "Estratto Conto API",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Mount ML router
if ml_router is not None:
    app.include_router(ml_router)
else:
    @app.get("/_router_missing")
    def router_missing():
        return {
            "error": "src.api.predizioni not loaded",
            "hint": "Create src/api/predizioni.py and ensure it defines 'router = APIRouter(prefix=\"/v1\")'.",
        }
