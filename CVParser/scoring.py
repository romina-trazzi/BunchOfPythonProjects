# scoring.py — calcolo % di completamento (presence-based, pesi semplici)

from __future__ import annotations
from typing import Any, Dict, Tuple

def _count_fields(x: Any) -> Tuple[int, int]:
    """Ritorna (totale_campi, campi_compilati) ricorsivo, stringhe non vuote = filled."""
    tot = 0; filled = 0
    if x is None:
        return 1, 0
    if isinstance(x, str):
        return 1, 1 if x.strip() else 0
    if isinstance(x, dict):
        for v in x.values():
            t, f = _count_fields(v)
            tot += t; filled += f
        return tot, filled
    if isinstance(x, list):
        if not x:
            return 1, 0
        for v in x:
            t, f = _count_fields(v)
            tot += t; filled += f
        return tot, filled
    # numeri/bool li consideriamo “presenti”
    return 1, 1

def completion(schema: Dict[str, Any]) -> float:
    tot, filled = _count_fields(schema)
    if tot == 0:
        return 0.0
    return round((filled / tot) * 100.0, 1)