from __future__ import annotations

from typing import List

from .agents.researcher import Researcher
from .agents.critic import Critic
from .agents.writer import Writer
from .models.job import JobItem
from .models.response import ExtractResponse
from .utils.logger import logger


def run_pipeline(job_title: str, city: str) -> ExtractResponse:
    """
    Orchestrazione semplice:
      1) Researcher -> raccoglie JobItem
      2) Critic     -> pulisce/deduplica/valida
      3) Writer     -> salva artefatti (MD + JSON [+ CSV]) in outputs/
      4) Ritorna ExtractResponse per l'API
    """
    try:
        researcher = Researcher()
        critic = Critic()
        writer = Writer()

        # 1) ricerca
        raw_items: List[JobItem] = researcher.run(job_title=job_title, city=city)

        # 2) pulizia
        clean_items: List[JobItem] = critic.run(raw_items, city=city)

        # 3) scrittura artefatti
        report_path = writer.run(clean_items, job_title=job_title, city=city)

        # 4) risposta API
        return ExtractResponse(
            job_title=job_title,
            city=city,
            count=len(clean_items),
            report_path=report_path,
            items=clean_items,
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        # In caso di errore, ritorna comunque una risposta coerente
        return ExtractResponse(
            job_title=job_title,
            city=city,
            count=0,
            report_path=None,
            items=[],
        )