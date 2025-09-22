# scoring.py — calcolo % di completamento
from __future__ import annotations
from typing import Any, Dict, Tuple, List

# ---------- Globale: presence-based, ricorsivo ----------
def _count_fields(x: Any) -> Tuple[int, int]:
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
    return 1, 1  # numeri/bool: presenti

def completion(schema: Dict[str, Any]) -> float:
    tot, filled = _count_fields(schema or {})
    if tot == 0:
        return 0.0
    return round((filled / tot) * 100.0, 1)

# ---------- Core: campi essenziali ----------
def _is_filled(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, list):
        if not v:
            return False
        return any(_is_filled(x) for x in v)
    if isinstance(v, dict):
        return any(_is_filled(x) for x in v.values())
    return True

def _take_first(items: Any) -> Dict[str, Any]:
    if isinstance(items, list) and items:
        x = items[0]
        return x if isinstance(x, dict) else {}
    return {}

def core_completion(schema: Dict[str, Any]) -> float:
    s = schema or {}
    an = s.get("anagrafica", {}) or {}
    ct = s.get("contatti", {}) or {}
    addr = (ct.get("indirizzo", {}) or {}) if isinstance(ct, dict) else {}
    exp0 = _take_first(s.get("esperienze_lavorative", []))
    edu0 = _take_first(s.get("istruzione", []))

    checks: List[bool] = [
        _is_filled(an.get("nome")),
        _is_filled(an.get("cognome")),
        _is_filled(ct.get("email")) or _is_filled(ct.get("telefono")) or _is_filled(ct.get("cellulare")),
        _is_filled(addr.get("citta")),
        _is_filled(addr.get("paese")),
        (_is_filled(exp0.get("posizione")) or _is_filled(exp0.get("azienda"))) and
        (_is_filled(exp0.get("data_inizio")) or _is_filled(exp0.get("data_fine"))),
        (_is_filled(edu0.get("titolo_studio")) or _is_filled(edu0.get("istituto"))) and
        (_is_filled(edu0.get("data_inizio")) or _is_filled(edu0.get("data_fine"))),
    ]
    total = len(checks)
    score = sum(1 for c in checks if c)
    return round((score / total) * 100.0, 1)

# ---------- Wrapper comodo ----------
def scores(schema: Dict[str, Any]) -> Dict[str, float]:
    return {
        "completezza_core_pct": core_completion(schema),
        "completezza_globale_pct": completion(schema),
    }
