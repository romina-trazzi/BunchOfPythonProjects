import csv
import os
import re
from typing import List, Dict


def _to_float(v):
    try:
        return float(str(v).replace(',', '.'))
    except Exception:
        return 0.0


def compute_alerts_from_pivot_csv(pivot_path: str, months: int = 3, tolerance: float = 0.2) -> Dict:
    if not os.path.exists(pivot_path):
        return {"alerts": [], "missing": True, "latest": None}
    month_cols: List[str] = []
    rows: List[Dict] = []
    with open(pivot_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fns = reader.fieldnames or []
        for fn in fns:
            if re.fullmatch(r"\d{4}-\d{2}", fn or ""):
                month_cols.append(fn)
        month_cols.sort()
        for row in reader:
            rows.append(row)
    if not month_cols:
        return {"alerts": [], "missing": True, "latest": None}
    latest = month_cols[-1]
    prev_cols = month_cols[:-1]
    prev_cols = prev_cols[-months:] if prev_cols else []
    alerts = []
    for row in rows:
        cat = row.get("Categoria") or row.get("category") or row.get("Category") or "Senza categoria"
        current = _to_float(row.get(latest))
        prev_vals = [_to_float(row.get(c)) for c in prev_cols]
        prev_vals = [v for v in prev_vals if v is not None]
        if len(prev_vals) == 0:
            continue
        avg = sum(prev_vals) / len(prev_vals)
        threshold = avg * (1.0 + tolerance)
        if current > threshold and current > 0:
            alerts.append({
                "categoria": cat,
                "mese": latest,
                "spesa": round(current, 2),
                "media": round(avg, 2),
                "soglia": round(threshold, 2)
            })
    return {"alerts": alerts, "missing": False, "latest": latest}