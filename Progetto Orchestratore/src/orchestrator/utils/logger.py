from __future__ import annotations

from pathlib import Path
from loguru import logger

# Assicura che la cartella outputs esista (evita errori su Windows)
Path("outputs").mkdir(parents=True, exist_ok=True)

# Aggiunge un sink su file + mantiene console
logger.remove()  # rimuove handler di default (console duplicata)
logger.add("outputs/app.log", rotation="1 MB", enqueue=True, backtrace=True, diagnose=False, level="INFO")
logger.add(lambda msg: print(msg, end=""))  # console pulita

__all__ = ["logger"]