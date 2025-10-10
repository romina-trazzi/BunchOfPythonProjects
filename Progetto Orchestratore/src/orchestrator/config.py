from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    SERPAPI_API_KEY: str | None = None

    SEARCH_ENGINE: str = "serpapi"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    HTTP_USER_AGENT: str = "orchestratore-agent/1.0"
    HTTP_MAX_RPS: int = 1

    # Carica automaticamente le variabili da .env
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()