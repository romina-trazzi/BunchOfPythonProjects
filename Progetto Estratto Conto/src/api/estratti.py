# src/api/estratti.py
# -------------------
# Purpose:
#   Read bank statement-like CSV data and expose minimal, filterable REST endpoints.
#
# Endpoints:
#   - GET /v1/estratti
#       Query params (all optional):
#         start_date, end_date    : ISO dates YYYY-MM-DD (filter by data_movimento, inclusive)
#         categoria               : exact match, case-insensitive
#         beneficiario            : exact match, case-insensitive
#         metodo_pagamento        : exact match, case-insensitive (e.g., POS, BONIFICO)
#         min_importo, max_importo: numeric range filter on absolute 'importo' value
#         order_by                : column to sort by (default: data_movimento)
#         order_dir               : 'asc' or 'desc' (default: asc)
#         limit, offset           : pagination (default: 100, 0)
#       Returns:
#         { count, limit, offset, items: [...] }
#
#   - GET /v1/estratti/{id_movimento}
#       Returns the single matching record or 404.
#
# Data source (inside the container):
#   - Preferred: /app/data/processed/mock_estratti_enriched.csv
#   - Fallback : /app/data/raw/mock_estratti.csv  (weekday/weekend/month are computed on the fly)
#
# Notes:
#   - Uses pandas for convenience; CSV is expected to use '.' as decimal separator.
#   - Returns plain dicts so we donâ€™t require pydantic models for this first step.
#   - FastAPI jsonable_encoder ensures numpy/pandas dtypes serialize cleanly to JSON.

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from typing import Optional, Dict, Any
import os
import pandas as pd
from datetime import datetime

router = APIRouter(prefix="/v1/estratti", tags=["estratti"])

# Container-visible default paths (aligned with docker-compose volume mounts)
PROCESSED_PATH = os.getenv("PROCESSED_CSV", "/app/data/processed/mock_estratti_enriched.csv")
RAW_PATH = os.getenv("RAW_CSV", "/app/data/raw/mock_estratti.csv")


def _parse_date(s: str) -> datetime:
    """Parse YYYY-MM-DD into a datetime.date-like object."""
    return datetime.strptime(s, "%Y-%m-%d")


def _ensure_enriched(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure 'giorno_settimana' (0=Mon..6=Sun), 'weekend' (0/1), and 'mese' (1-12) exist.
    This is used when we load from RAW and must compute these columns on the fly.
    """
    # Parse dates if not already parsed
    if not pd.api.types.is_datetime64_any_dtype(df["data_movimento"]):
        df["data_movimento"] = pd.to_datetime(df["data_movimento"], format="%Y-%m-%d", errors="coerce")
    if not pd.api.types.is_datetime64_any_dtype(df["data_valuta"]):
        df["data_valuta"] = pd.to_datetime(df["data_valuta"], format="%Y-%m-%d", errors="coerce")

    # Compute derived columns if missing
    if "giorno_settimana" not in df.columns:
        df["giorno_settimana"] = df["data_movimento"].dt.weekday  # 0=Mon .. 6=Sun
    if "weekend" not in df.columns:
        df["weekend"] = (df["giorno_settimana"] >= 5).astype(int)  # Sat/Sun -> 1
    if "mese" not in df.columns:
        df["mese"] = df["data_movimento"].dt.month

    return df


def _load_df() -> pd.DataFrame:
    """
    Load processed CSV if present; otherwise load raw CSV and enrich it.
    Raise 503 if no suitable file is present.
    """
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH)
        # Ensure date columns are parsed for filtering/sorting
        df["data_movimento"] = pd.to_datetime(df["data_movimento"], errors="coerce")
        df["data_valuta"] = pd.to_datetime(df["data_valuta"], errors="coerce")
        return df

    if os.path.exists(RAW_PATH):
        df = pd.read_csv(RAW_PATH)
        df = _ensure_enriched(df)
        return df

    raise HTTPException(status_code=503, detail="No CSV data found under /app/data.")


def _ci_equal(a: Optional[str], b: Optional[str]) -> bool:
    """Case-insensitive equality for optional strings."""
    if a is None or b is None:
        return False
    return a.strip().lower() == b.strip().lower()


@router.get("", summary="List statements with filters and pagination")
def list_estratti(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD (filter by data_movimento, inclusive)"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD (filter by data_movimento, inclusive)"),
    categoria: Optional[str] = Query(None, description="Exact match, case-insensitive"),
    beneficiario: Optional[str] = Query(None, description="Exact match, case-insensitive"),
    metodo_pagamento: Optional[str] = Query(None, description="Exact match, case-insensitive (e.g., POS)"),
    min_importo: Optional[float] = Query(None, description="Minimum absolute 'importo'"),
    max_importo: Optional[float] = Query(None, description="Maximum absolute 'importo'"),
    order_by: str = Query("data_movimento", description="Column to sort by"),
    order_dir: str = Query("asc", pattern="^(?i)(asc|desc)$", description="Sort direction"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Start index"),
) -> Dict[str, Any]:
    """
    Load the CSV, apply filters, sort, and return a slice (offset, limit).
    Designed for quick exploration and mock usage, not big-data workloads.
    """
    df = _load_df()

    # Filter by date range
    if start_date:
        sd = _parse_date(start_date)
        df = df[df["data_movimento"] >= sd]
    if end_date:
        ed = _parse_date(end_date)
        df = df[df["data_movimento"] <= ed]

    # Exact, case-insensitive filters on text columns
    if categoria:
        df = df[df["categoria"].astype(str).str.lower() == categoria.strip().lower()]
    if beneficiario:
        df = df[df["beneficiario"].astype(str).str.lower() == beneficiario.strip().lower()]
    if metodo_pagamento:
        df = df[df["metodo_pagamento"].astype(str).str.lower() == metodo_pagamento.strip().lower()]

    # Numeric range on absolute amount
    if min_importo is not None:
        df = df[df["importo"].abs() >= float(min_importo)]
    if max_importo is not None:
        df = df[df["importo"].abs() <= float(max_importo)]

    # Sorting
    if order_by not in df.columns:
        order_by = "data_movimento"
    ascending = order_dir.lower() == "asc"
    df = df.sort_values(by=order_by, ascending=ascending)

    total = len(df)
    page = df.iloc[offset : offset + limit]

    # Convert to JSON-serializable objects
    # Ensure dates become ISO strings
    if pd.api.types.is_datetime64_any_dtype(page["data_movimento"]):
        page["data_movimento"] = page["data_movimento"].dt.strftime("%Y-%m-%d")
    if pd.api.types.is_datetime64_any_dtype(page["data_valuta"]):
        page["data_valuta"] = page["data_valuta"].dt.strftime("%Y-%m-%d")

    items = jsonable_encoder(page.to_dict(orient="records"))

    return {
        "count": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/{id_movimento}", summary="Get a single statement by id_movimento")
def get_estratto(id_movimento: str) -> Dict[str, Any]:
    """
    Return the record whose 'id_movimento' exactly matches the path parameter.
    """
    df = _load_df()
    mask = df["id_movimento"].astype(str) == id_movimento
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"id_movimento '{id_movimento}' not found")

    row = df.loc[mask].copy()

    # Ensure ISO dates for JSON
    if pd.api.types.is_datetime64_any_dtype(row["data_movimento"]):
        row["data_movimento"] = row["data_movimento"].dt.strftime("%Y-%m-%d")
    if pd.api.types.is_datetime64_any_dtype(row["data_valuta"]):
        row["data_valuta"] = row["data_valuta"].dt.strftime("%Y-%m-%d")

    # Return the first (and should be only) match
    payload = jsonable_encoder(row.iloc[0].to_dict())
    return payload

