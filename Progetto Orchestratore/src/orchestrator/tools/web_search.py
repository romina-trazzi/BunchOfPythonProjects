from __future__ import annotations

import time
from typing import List
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import httpx
from bs4 import BeautifulSoup

from ..clients.ai import expand_keywords
from ..config import settings


def _dedup_keep_order(urls: List[str], limit: int) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for u in urls:
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    return out


def _is_linkedin_job(url: str) -> bool:
    """
    Accetta solo URL plausibili di annunci LinkedIn.
    (esempi reali: https://www.linkedin.com/jobs/view/<id>/)
    """
    try:
        p = urlparse(url)
        if "linkedin.com" not in p.netloc:
            return False
        return p.path.startswith("/jobs/view") or "/jobs/view/" in p.path or p.path.startswith("/jobs/search")
    except Exception:
        return False


def _ddg_unwrap(href: str) -> str:
    """
    Nei risultati DuckDuckGo HTML, i link possono essere redirect:
      https://duckduckgo.com/l/?uddg=<URL-ENCODED>
    Qui estraiamo l'URL reale.
    """
    try:
        p = urlparse(href)
        if "duckduckgo.com" in p.netloc and p.path.startswith("/l/"):
            qs = parse_qs(p.query or "")
            if "uddg" in qs and qs["uddg"]:
                return unquote(qs["uddg"][0])
    except Exception:
        pass
    return href


def _ddg_search(query: str, max_results: int = 15) -> List[str]:
    """
    Ricerca best-effort su DuckDuckGo HTML (senza API).
    Ritorna una lista di URL (filtrati più tardi da _is_linkedin_job).
    """
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}&kl=it-it"
    headers = {"User-Agent": settings.HTTP_USER_AGENT}
    try:
        r = httpx.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        urls: List[str] = []

        # Heuristics: prendi tutti i <a> con href http/https
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http"):
                urls.append(_ddg_unwrap(href))
            elif href.startswith("/l/?"):
                urls.append(_ddg_unwrap("https://duckduckgo.com" + href))

            if len(urls) >= max_results:
                break

        return urls
    except Exception:
        return []


def _linkedin_search_pages(keywords: List[str], city: str) -> List[str]:
    """
    Costruisce direttamente URL di ricerca LinkedIn Jobs (pagine public).
    Anche se spesso richiedono login, possono tornare almeno un <title>
    utile allo scraper 'enrich_from_page'.
    """
    base = "https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}"
    loc = quote_plus(city)
    urls = []
    for kw in keywords:
        urls.append(base.format(kw=quote_plus(kw), loc=loc))
    return urls


def search_jobs_linkedin(job_title: str, city: str, limit: int = 30) -> List[str]:
    """
    Cerca URL di offerte LinkedIn con:
      1) Varianti keyword generate da Anthropic (expand_keywords)
      2) Ricerche DuckDuckGo con filtro site:linkedin.com/jobs
      3) URL diretti di pagine 'jobs/search' di LinkedIn
    Ritorna una lista deduplicata di URL (max `limit`).
    """
    # 1) Varianti con LLM (o fallback interno se chiave non presente)
    variants = expand_keywords(job_title, city, n=5)

    candidate_urls: List[str] = []

    # 2) Site search su DDG per ogni variante
    #    Esempio query: site:linkedin.com/jobs "Data Scientist" "Milano"
    headers = {"User-Agent": settings.HTTP_USER_AGENT}
    per_variant = max(3, limit // max(1, len(variants)))
    for i, kw in enumerate(variants, start=1):
        q = f'site:linkedin.com/jobs "{kw}" "{city}"'
        urls = _ddg_search(q, max_results=per_variant * 3)  # un po' più abbondante, poi filtriamo
        for u in urls:
            if _is_linkedin_job(u):
                candidate_urls.append(u)

        # rate limit gentile tra query per non martellare
        time.sleep(0.6)

    # 3) Aggiungi URL delle pagine di ricerca LinkedIn (utile come fallback)
    candidate_urls.extend(_linkedin_search_pages(variants, city))

    # 4) Dedup e taglio a 'limit'
    return _dedup_keep_order(candidate_urls, limit)