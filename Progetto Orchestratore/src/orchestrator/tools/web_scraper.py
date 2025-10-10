from __future__ import annotations
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from ..models.job import JobItem
from ..config import settings

def enrich_from_page(url: str, city: str) -> Optional[JobItem]:

    try:
        r = httpx.get(url, headers={"User-Agent": settings.HTTP_USER_AGENT}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.text.strip() if soup.title else "Job"
        return JobItem(title=title, company=None, city=city, url=url, source="web")
    except Exception:
        return None