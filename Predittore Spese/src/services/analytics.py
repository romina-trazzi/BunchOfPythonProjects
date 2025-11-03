from collections import defaultdict
from typing import Dict, List, Tuple
from src.domain.models import Transaction


def ym(d) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def aggregate_monthly(txs: List[Transaction]) -> Dict[str, Dict[str, float]]:
    agg: Dict[str, Dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in txs:
        k = ym(t.date)
        if (t.type or "").lower() == "credito" or t.amount > 0:
            agg[k]["income"] += abs(t.amount)
        else:
            agg[k]["expense"] += abs(t.amount)
    return agg


def pivot_expense_by_category_monthly(txs: List[Transaction]) -> Tuple[List[str], Dict[str, Dict[str, float]]]:
    months_set = set()
    pivot: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for t in txs:
        m = ym(t.date)
        months_set.add(m)
        if (t.type or "").lower() == "debito" or t.amount < 0:
            cat = (t.category or "Senza categoria")
            pivot[cat][m] += abs(t.amount)
    months = sorted(list(months_set))
    return months, pivot