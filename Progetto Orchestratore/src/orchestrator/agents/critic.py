from __future__ import annotations

from typing import List

from .base import Agent
from ..models.job import JobItem


class Critic(Agent):
    """
    Pulisce e valida i risultati del Researcher.

    - Rimuove duplicati (priorità: URL; fallback: titolo+azienda).
    - Scarta record senza titolo.
    - Se la città è presente nell'item, deve combaciare con la città richiesta.
    """

    name = "critic"

    def run(self, items: List[JobItem], city: str) -> List[JobItem]:
        self.log_info("Start cleaning", incoming=len(items), city=city)

        def _norm(s: str | None) -> str:
            return (s or "").strip().lower()

        seen: set[str] = set()
        cleaned: List[JobItem] = []

        for it in items:
            # requisito minimo: titolo
            if not _norm(it.title):
                continue

            # chiave dedup: URL se presente, altrimenti titolo+azienda
            key = it.url if it.url else f"{_norm(it.title)}|{_norm(it.company)}"
            if key in seen:
                continue
            seen.add(key)

            # filtro città: se l'item ha city valorizzata, deve combaciare
            if _norm(it.city) and _norm(it.city) != _norm(city):
                continue

            cleaned.append(it)

        self.log_info("Cleaning done", outgoing=len(cleaned))
        return cleaned