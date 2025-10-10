from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
import orjson

from .base import Agent
from ..models.job import JobItem
from ..utils.logger import logger


class Writer(Agent):
    """
    Confeziona l'output finale:
      - Crea un report Markdown (tabellare).
      - Salva un **file JSON completo** con metadati e risultati.
      - (Opzionale) Esporta anche CSV.
    Ritorna: percorso del file Markdown creato.
    """

    name = "writer"

    def _safe_slug(self, text: str) -> str:
        # minuscole, spazi -> -, rimuove tutto ciò che non è [a-z0-9-_]
        slug = re.sub(r"\s+", "-", text.strip().lower())
        slug = re.sub(r"[^a-z0-9\-_]+", "", slug)
        return slug or "report"

    def run(self, items: List[JobItem], job_title: str, city: str) -> str:
        Path("outputs").mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{self._safe_slug(job_title)}_{self._safe_slug(city)}_{ts}"

        md_path = Path("outputs") / f"report_{base}.md"
        json_path = Path("outputs") / f"results_{base}.json"
        csv_path = Path("outputs") / f"jobs_{base}.csv"  # opzionale

        # ---------- Markdown ----------
        lines: list[str] = []
        lines.append(f"# Offerte per **{job_title}** a **{city}**")
        lines.append("")
        lines.append(f"- Generato: {datetime.now().isoformat(timespec='seconds')}")
        lines.append(f"- Totale risultati: **{len(items)}**")
        lines.append("")
        if items:
            lines.append("| Titolo | Azienda | Città | Link | Fonte |")
            lines.append("|---|---|---|---|---|")
            for it in items:
                title = it.title.replace("|", " ")
                company = (it.company or "-").replace("|", " ")
                icity = (it.city or city).replace("|", " ")
                link = f"[apri]({it.url})" if it.url else "-"
                source = it.source or "-"
                lines.append(f"| {title} | {company} | {icity} | {link} | {source} |")
        else:
            lines.append("_Nessun risultato._")

        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # ---------- JSON COMPLETO ----------
        try:
            payload = {
                "job_title": job_title,
                "city": city,
                "count": len(items),
                "report_path": str(md_path),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "items": [it.model_dump() for it in items],
            }
            json_bytes = orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)
            json_path.write_bytes(json_bytes)
        except Exception as e:
            logger.bind(agent=self.name).error("Failed to write JSON", error=str(e))

        # ---------- CSV (opzionale) ----------
        try:
            if items:
                df = pd.DataFrame([it.model_dump() for it in items])
                df.to_csv(csv_path, index=False, encoding="utf-8")
        except Exception as e:
            logger.bind(agent=self.name).error("Failed to write CSV", error=str(e))

        self.log_info(
            "Artifacts written",
            md=str(md_path),
            json=str(json_path),
            csv=str(csv_path),
            total=len(items),
        )
        return str(md_path)