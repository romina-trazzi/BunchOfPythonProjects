from __future__ import annotations

import time
from typing import List

from .base import Agent
from ..models.job import JobItem
from ..tools.web_search import search_jobs_linkedin
from ..tools.web_scraper import enrich_from_page
from ..utils.logger import logger
from ..config import settings


class Researcher(Agent):
    """
    Ricerca offerte di lavoro a partire da (job_title, city).

    Passi:
      1) Usa il tool di web search (SerpAPI: engine=linkedin_jobs) per ottenere una lista di URL.
      2) Per ogni URL, esegue uno scraping leggero (pubblico) per estrarre titolo/azienda/città/link.
      3) Ritorna una lista di JobItem (best effort).

    Note:
    - Rispetta un semplice rate-limit letto da settings.HTTP_MAX_RPS (default 1 req/sec).
    - Se SERPAPI_API_KEY non è presente, la lista URL potrebbe essere vuota (fallback minimale).
    """

    name = "researcher"

    def run(self, job_title: str, city: str, limit: int = 30) -> List[JobItem]:
        self.log_info("Starting search", job_title=job_title, city=city)

        # 1) Cerca URL delle offerte (LinkedIn Jobs via SerpAPI)
        urls = search_jobs_linkedin(job_title=job_title, city=city) or []
        if not urls:
            self.log_info("No URLs from search (check SERPAPI key or query).")
            return []

        # dedup e limite massimo
        deduped = []
        seen = set()
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                deduped.append(u)
            if len(deduped) >= limit:
                break

        self.log_info("Collected URLs", count=len(deduped))

        # 2) Scraping leggero con rate limit
        items: List[JobItem] = []
        delay = 1.0 / max(1, int(settings.HTTP_MAX_RPS))  # es. 1 req/sec

        for idx, url in enumerate(deduped, start=1):
            try:
                job = enrich_from_page(url, city=city)
                if job:
                    items.append(job)
                    logger.bind(agent=self.name).info(
                        "Parsed job",
                        idx=idx,
                        title=job.title,
                        source=job.source,
                    )
                else:
                    logger.bind(agent=self.name).info("Skipped empty parse", idx=idx, url=url)
            except Exception as e:
                self.log_error("Error scraping page", url=url, error=str(e))
            finally:
                # Rate limit semplice tra richieste
                if idx < len(deduped):
                    time.sleep(delay)

        self.log_info("Finished search", total=len(items))
        return items