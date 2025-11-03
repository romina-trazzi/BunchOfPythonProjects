import csv
import os
from typing import List
from datetime import datetime
from src.domain.models import Transaction

DATE_KEYS = ["data", "date"]
DESC_KEYS = ["descrizione", "description"]
AMOUNT_KEYS = ["importo", "amount"]
TYPE_KEYS = ["tipo", "type"]
CATEGORY_KEYS = ["categoria", "category"]


def _get(row, keys, default=""):
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return default


def read_transactions(csv_path: str) -> List[Transaction]:
    txs: List[Transaction] = []
    if not os.path.exists(csv_path):
        return txs
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ds = _get(row, DATE_KEYS)
            d = datetime.strptime(ds, "%Y-%m-%d").date() if ds else None
            desc = _get(row, DESC_KEYS)
            amount_s = _get(row, AMOUNT_KEYS, "0")
            try:
                amount = float(str(amount_s).replace(',', '.'))
            except Exception:
                amount = 0.0
            t = _get(row, TYPE_KEYS, "")
            cat = _get(row, CATEGORY_KEYS, None)
            if d is None:
                continue
            txs.append(Transaction(date=d, description=desc, amount=amount, type=t, category=cat))
    return txs


def write_csv(rows, path: str, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)