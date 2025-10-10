from __future__ import annotations

from typing import List

from ..config import settings

# Import "soft": il progetto parte anche senza la libreria installata.
try:
    import anthropic
except Exception:  # pragma: no cover
    anthropic = None


def _get_client() -> "anthropic.Anthropic | None":
    """Ritorna il client Anthropic se disponibile e configurato, altrimenti None."""
    if anthropic is None:
        return None
    if not settings.ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def expand_keywords(job_title: str, city: str, n: int = 5) -> List[str]:
    """
    Usa Anthropic per proporre varianti/sinonimi utili alla ricerca.
    Se la chiave non è configurata, ritorna una fallback minimale.
    """
    base = [job_title]
    if city and city.lower() not in job_title.lower():
        base.append(f"{job_title} {city}")

    client = _get_client()
    if client is None:
        # Fallback semplice senza LLM
        jt = job_title.lower()
        synonyms = []
        if "data scientist" in jt:
            synonyms = ["machine learning engineer", "ml scientist", "ai engineer"]
        elif "developer" in jt or "sviluppatore" in jt:
            synonyms = ["software engineer", "programmatore", "full stack developer"]
        else:
            synonyms = []
        # restituisce (base + sinonimi) limitati a n
        out = list(dict.fromkeys(base + synonyms))[: max(1, n)]
        return out

    prompt = (
        "Sei un assistente che genera varianti di keyword per cercare offerte di lavoro.\n"
        f"Titolo: {job_title}\nCittà: {city}\n"
        "Restituisci una lista breve (max {n}) di frasi-chiave diverse, solo una per riga, senza numeri né punteggiatura."
    )

    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=200,
            temperature=0.3,
            system="Genera varianti concise utili per la ricerca di job postings.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in msg.content:
            # content può essere una lista di blocchi (testo, tool_use, ecc.)
            if getattr(block, "type", None) == "text":
                text += block.text + "\n"
        # normalizza in righe non vuote
        variants = [line.strip() for line in text.splitlines() if line.strip()]
        # aggiungi sempre la keyword originale in testa
        variants = list(dict.fromkeys(base + variants))
        return variants[: max(1, n)]
    except Exception:
        # in caso di problemi con l'API, fallback
        return list(dict.fromkeys(base))[: max(1, n)]
