# src/data/generator.py
# ---------------------
# Purpose:
#   Generate 12 months of realistic synthetic bank transactions with multiple behavioral patterns.
#
# Generation logic includes:
#   1. FIXED RECURRING TRANSACTIONS:
#      - Monthly salary (income)
#      - Monthly rent
#      - Utilities: electricity, gas, internet
#      - Streaming subscription
#
#   2. VARIABLE SPENDING:
#      - Groceries several times per month
#      - Restaurants a few times per month
#      - Phone top-ups
#      - ATM withdrawals
#
#   3. SEASONAL VARIABILITY:
#      - December â†’ +40% shopping/restaurant/groceries spending
#      - January â†’ +20% gas/electricity (cold months)
#      - August â†’ âˆ’30% all variable spending (vacation period)
#
#   4. WEEKEND PATTERN:
#      - Higher probability of restaurants and grocery transactions on Sat/Sun
#
#   5. ANOMALIES:
#      - 1â€“2 "unexpected" expenses per year (category: Altro/Imprevisto, high amount)
#      - 1 "extra income" per year (e.g. tax refund or bonus)
#
#   6. RANDOM NOISE:
#      - Each amount drawn from normal distribution (mean Â± sd)
#      - Â±15% additive noise applied to variable transactions
#
# Output:
#   data/raw/sample_data.csv (or /app/data/raw/sample_data.csv in Docker)
#
# How to run:
#   > python -m src.data.generator
#   or (inside Docker)
#   > docker exec -it estratto_conto_api python -m src.data.generator
#
# Notes:
#   - Deterministic with fixed random seed (change GEN_SEED to vary output).
#   - Designed to look plausible but still fully synthetic.

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict
import calendar
import numpy as np
import pandas as pd

# ---------- Configuration ----------
SEED = int(os.getenv("GEN_SEED", "42"))
MONTHS = int(os.getenv("GEN_MONTHS", "12"))
START_DATE_STR = os.getenv("GEN_START_DATE", None)
START_BALANCE = float(os.getenv("GEN_START_BALANCE", "1000.00"))

@dataclass
class Baselines:
    salary_mean: float = 2500.0
    salary_sd: float = 200.0
    rent_mean: float = 650.0
    rent_sd: float = 30.0
    electricity_mean: float = 80.0
    electricity_sd: float = 20.0
    gas_mean: float = 70.0
    gas_sd: float = 25.0
    internet_mean: float = 30.0
    internet_sd: float = 8.0
    streaming_mean: float = 13.0
    streaming_sd: float = 2.0
    grocery_mean: float = 45.0
    grocery_sd: float = 20.0
    restaurant_mean: float = 25.0
    restaurant_sd: float = 15.0
    phone_topup_mean: float = 10.0
    phone_topup_sd: float = 5.0
    atm_withdraw_mean: float = 60.0
    atm_withdraw_sd: float = 20.0

BASE = Baselines()

# ---------- Helpers ----------
def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def _default_out_path() -> Path:
    if Path("/app").exists():
        return Path("/app/data/sample_data.csv")
    return _project_root() / "data" / "sample_data.csv"

def _clamp_day(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(max(day, 1), last_day))

def _amount(mean: float, sd: float, rng: np.random.Generator, min_val: float = 1.0) -> float:
    """Return a positive amount drawn from normal distribution."""
    val = rng.normal(mean, sd)
    return float(max(round(val, 2), min_val))

def _row(
    dmov: date,
    descrizione: str,
    categoria: str,
    sottocategoria: str,
    importo_pos: float,
    segno: int,
    metodo: str,
    beneficiario: str,
    idx: int,
) -> Dict[str, object]:
    dval = dmov + timedelta(days=1)
    return {
        "data_movimento": dmov.strftime("%Y-%m-%d"),
        "data_valuta": dval.strftime("%Y-%m-%d"),
        "descrizione": descrizione,
        "categoria": categoria,
        "sottocategoria": sottocategoria,
        "importo": round(importo_pos, 2),
        "segno": segno,
        "saldo_disponibile": None,
        "metodo_pagamento": metodo,
        "beneficiario": beneficiario,
        "id_movimento": f"TX{dmov.strftime('%Y%m%d')}{idx:03d}",
    }

# ---------- Seasonal and weekend multipliers ----------
def _seasonal_factor(month: int, category: str) -> float:
    """Return a seasonal multiplier for given month and category."""
    # Default 1.0
    if month == 12 and category in ["Spesa", "Ristorante", "Shopping"]:
        return 1.4
    if month == 1 and category == "Utenze":
        return 1.2
    if month == 8:
        return 0.7
    return 1.0

def _weekend_bias(d: date, category: str, rng: np.random.Generator) -> bool:
    """Higher probability for weekend transactions on certain categories."""
    weekday = d.weekday()  # 0=Mon .. 6=Sun
    if category in ["Ristorante", "Spesa"]:
        if weekday >= 5:  # Sat/Sun
            return rng.random() < 0.6  # more likely
        else:
            return rng.random() < 0.3
    return rng.random() < 0.1

# ---------- Generation logic ----------
def generate(year_start: int, month_start: int, months: int, seed: int, start_balance: float) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: List[Dict[str, object]] = []
    idx = 1
    y, m = year_start, month_start

    for _ in range(months):
        # salary (income)
        salary_day = _clamp_day(y, m, 10)
        rows.append(_row(salary_day, f"Stipendio {y}-{m:02d}", "Bonifico", "In",
                         _amount(BASE.salary_mean, BASE.salary_sd, rng), +1, "BONIFICO", "Azienda SRL", idx)); idx += 1

        # rent (fixed expense)
        rent_day = _clamp_day(y, m, 14)
        rows.append(_row(rent_day, "Addebito canone", "Affitto", "Canone",
                         _amount(BASE.rent_mean, BASE.rent_sd, rng), -1, "POS", "Proprietario", idx)); idx += 1

        # utilities (Utenze)
        for sub, mean, sd in [("Luce", BASE.electricity_mean, BASE.electricity_sd),
                              ("Gas", BASE.gas_mean, BASE.gas_sd),
                              ("Internet", BASE.internet_mean, BASE.internet_sd)]:
            d = _clamp_day(y, m, int(rng.integers(5, 25)))
            seasonal = _seasonal_factor(m, "Utenze")
            amt = _amount(mean * seasonal, sd, rng)
            rows.append(_row(d, "Addebito utenza", "Utenze", sub, amt, -1, "POS", "Enel Energia", idx)); idx += 1

        # streaming
        d = _clamp_day(y, m, 3)
        amt = _amount(BASE.streaming_mean, BASE.streaming_sd, rng)
        rows.append(_row(d, "Addebito abbonamento", "Abbonamenti", "Streaming", amt, -1, "POS", "Netflix", idx)); idx += 1

        # groceries and restaurants (variable)
        for day in range(1, calendar.monthrange(y, m)[1] + 1):
            d = date(y, m, day)
            # groceries
            if _weekend_bias(d, "Spesa", rng):
                seasonal = _seasonal_factor(m, "Spesa")
                amt = _amount(BASE.grocery_mean * seasonal, BASE.grocery_sd, rng)
                rows.append(_row(d, "Pagamento POS Supermercato", "Spesa", "Supermercato",
                                 amt, -1, "POS", rng.choice(["Esselunga", "Coop", "Conad"]), idx)); idx += 1
            # restaurants
            if _weekend_bias(d, "Ristorante", rng):
                seasonal = _seasonal_factor(m, "Ristorante")
                amt = _amount(BASE.restaurant_mean * seasonal, BASE.restaurant_sd, rng)
                rows.append(_row(d, "Pagamento POS Ristorante", "Ristorante", "Pranzo",
                                 amt, -1, "POS", rng.choice(["Trattoria da Nino", "Osteria del Corso"]), idx)); idx += 1

        # phone top-ups (1â€“3)
        for _ in range(int(rng.integers(1, 4))):
            d = _clamp_day(y, m, int(rng.integers(1, 28)))
            amt = _amount(BASE.phone_topup_mean, BASE.phone_topup_sd, rng)
            rows.append(_row(d, "Ricarica telefonica", "Telefonia", "Ricarica",
                             amt, -1, "POS", rng.choice(["TIM", "Vodafone", "Iliad"]), idx)); idx += 1

        # ATM withdrawals (0â€“2)
        for _ in range(int(rng.integers(0, 3))):
            d = _clamp_day(y, m, int(rng.integers(1, 28)))
            amt = _amount(BASE.atm_withdraw_mean, BASE.atm_withdraw_sd, rng)
            rows.append(_row(d, "Prelievo contante", "Prelievo", "Bancomat",
                             amt, -1, "BANCOMAT", "ATM Intesa", idx)); idx += 1

        # occasional random one-offs
        if rng.random() < 0.3:  # ~3â€“4 months per year
            d = _clamp_day(y, m, int(rng.integers(1, 28)))
            amt = _amount(rng.uniform(30, 150), rng.uniform(10, 50), rng)
            cat = rng.choice(["Salute", "Shopping", "Trasporti", "Altro"])
            sub = rng.choice(["Farmacia", "Abbigliamento", "Carburante", "Imprevisto"])
            rows.append(_row(d, f"Spesa straordinaria {cat}", cat, sub, amt, -1, "POS", "Esercente", idx)); idx += 1

        # anomalies (rare high values)
        if rng.random() < 0.15:
            d = _clamp_day(y, m, int(rng.integers(1, 28)))
            amt = round(rng.uniform(400, 1200), 2)
            rows.append(_row(d, "Spesa anomala", "Altro", "Imprevisto", amt, -1, "POS", "Evento straordinario", idx)); idx += 1
        if rng.random() < 0.15:
            d = _clamp_day(y, m, int(rng.integers(1, 28)))
            amt = round(rng.uniform(300, 1000), 2)
            rows.append(_row(d, "Accredito imprevisto", "Bonifico", "Bonus", amt, +1, "BONIFICO", "Azienda SRL", idx)); idx += 1

        # next month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    # Build DataFrame
    df = pd.DataFrame(rows).sort_values("data_movimento").reset_index(drop=True)

    # Compute running balance
    df["importo"] = df["importo"].astype(float).round(2)
    df["segno"] = df["segno"].astype(int)
    df["saldo_disponibile"] = (START_BALANCE + (df["importo"] * df["segno"]).cumsum()).round(2)
    return df

# ---------- Entry point ----------
def main() -> int:
    if START_DATE_STR:
        try:
            start = datetime.strptime(START_DATE_STR, "%Y-%m-%d").date()
        except ValueError:
            raise SystemExit("GEN_START_DATE must be YYYY-MM-DD")
    else:
        today = date.today()
        start = date(today.year, 1, 1)

    df = generate(start.year, start.month, MONTHS, SEED, START_BALANCE)
    out_path = Path(os.getenv("OUT_CSV", str(_default_out_path())))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[GEN] Wrote {len(df)} rows -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
