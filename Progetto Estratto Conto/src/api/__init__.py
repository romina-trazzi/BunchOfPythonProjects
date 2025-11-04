from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.predizioni import router as ml_router
from src.api.estratti import router as estratti_router

app = FastAPI(title="Progetto Estratto Conto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # per debug, accetta tutte le origini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ml_router)
app.include_router(estratti_router)