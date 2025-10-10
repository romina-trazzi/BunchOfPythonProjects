from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

try:
    from ..utils.logger import logger  # preferito: stesso logger con sink su file
except Exception:  # ImportError o altri
    from loguru import logger  # fallback: almeno logga in console


class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def log_info(self, message: str, **extra: Any) -> None:
        logger.bind(agent=self.name, **extra).info(message)

    def log_error(self, message: str, **extra: Any) -> None:
        logger.bind(agent=self.name, **extra).error(message)