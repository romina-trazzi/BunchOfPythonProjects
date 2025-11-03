# src/data/preprocessor.py
# ------------------------
# Provides a minimal, circular-import-free preprocessing layer for tabular data:
# - build_preprocessor(cfg) -> sklearn ColumnTransformer that fits/transforms
# - make_Xy(df, cfg, transformer, fit_transform=False) -> (X, y, df_out)
#
# Expectations from cfg (default.yaml), keys are optional and safely inferred:
#   cfg["features"]["target_column"]       : str (e.g., "importo")
#   cfg["features"]["id_column"]           : str (e.g., "id_movimento")
#   cfg["features"]["drop_columns"]        : list[str]
#   cfg["features"]["numeric_columns"]     : list[str]
#   cfg["features"]["categorical_columns"] : list[str]
#   cfg["features"]["date_columns"]        : list[str] (e.g., ["data_movimento"])
#   cfg["features"]["use_weekday"]         : bool
#   cfg["features"]["use_month"]           : bool
#   cfg["features"]["use_weekend"]         : bool
#
# Notes:
# - Date-features are engineered in make_Xy (weekday/month/weekend) and treated as numeric.
# - When a list (numeric/categorical/date) is not provided, we infer from dtypes.
# - df_out returned by make_Xy is a shallow copy with id/target preserved for debugging.

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# -----------------------------
# Helpers to read cfg safely
# -----------------------------
def _get(cfg: Dict[str, Any], path: List[str], default=None):
    cur = cfg
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _as_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


# --------------------------------------
# 1) Build sklearn ColumnTransformer
# --------------------------------------
def build_preprocessor(cfg: Dict[str, Any]) -> ColumnTransformer:
    """Return a ColumnTransformer using numeric/categorical columns from cfg or inferred."""
    feats = _get(cfg, ["features"], {}) or {}

    # Declared columns (optional)
    numeric_declared      = _as_list(feats.get("numeric_columns"))
    categorical_declared  = _as_list(feats.get("categorical_columns"))
    date_columns          = _as_list(feats.get("date_columns"))

    # We cannot infer from data here (no df available), so we rely on declared lists.
    # If not declared, we will infer in make_Xy and pass consistent set to transformer
    # by fitting on the first call with fit_transform=True.

    # Build pipelines
    numeric_pipeline = StandardScaler(with_mean=True, with_std=True)
    categorical_pipeline = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    # Use placeholders; actual column lists will be bound on first fit via make_Xy.
    # ColumnTransformer allows unknown columns at transform time if we keep names stable.
    ct = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_declared + _engineered_numeric_names(feats)),
            ("cat", categorical_pipeline, categorical_declared),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
        sparse_threshold=0.0,
    )
    return ct


# ----------------------------------------------------
# 2) Feature engineering + matrix assembly (X, y, df)
# ----------------------------------------------------
def make_Xy(
    df: pd.DataFrame,
    cfg: Dict[str, Any],
    transformer: ColumnTransformer,
    fit_transform: bool = False,
) -> Tuple[np.ndarray, Optional[np.ndarray], pd.DataFrame]:
    """
    Create features and apply the provided ColumnTransformer.
    Returns (X, y, df_out) where:
      - X is the numeric 2D matrix for the estimator
      - y is target vector or None if target missing
      - df_out is a copy for inspection (keeps id/target and some context)
    """

    df = df.copy()

    feats = _get(cfg, ["features"], {}) or {}
    target_col = feats.get("target_column", "importo")
    id_col     = feats.get("id_column", "id_movimento")
    drop_cols  = set(_as_list(feats.get("drop_columns")))
    date_cols  = _as_list(feats.get("date_columns"))

    # ---- 2.1 Parse/engineer date features (weekday/month/weekend) ----
    use_weekday = bool(feats.get("use_weekday", True))
    use_month   = bool(feats.get("use_month", True))
    use_weekend = bool(feats.get("use_weekend", True))

    if date_cols:
        for col in date_cols:
            if col in df.columns:
                # parse to datetime safely
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=False)
                # engineer numeric features
                if use_weekday:
                    df[f"{col}_weekday"] = df[col].dt.weekday.astype("Int64")
                if use_month:
                    df[f"{col}_month"] = df[col].dt.month.astype("Int64")
                if use_weekend:
                    # weekend = 1 if Sat(5) or Sun(6)
                    df[f"{col}_weekend"] = df[col].dt.weekday.isin([5, 6]).astype("Int64")

    # Collect engineered numeric names actually present
    engineered = []
    for col in date_cols:
        if use_weekday and f"{col}_weekday" in df.columns:
            engineered.append(f"{col}_weekday")
        if use_month and f"{col}_month" in df.columns:
            engineered.append(f"{col}_month")
        if use_weekend and f"{col}_weekend" in df.columns:
            engineered.append(f"{col}_weekend")

    # ---- 2.2 Determine numeric/categorical columns (infer if not provided) ----
    numeric_declared     = _as_list(feats.get("numeric_columns"))
    categorical_declared = _as_list(feats.get("categorical_columns"))

    numeric_inferred = []
    categorical_inferred = []

    if not numeric_declared or not categorical_declared:
        # Infer basic types from dataframe dtypes
        for c in df.columns:
            if c in drop_cols:
                continue
            if c == target_col or c == id_col:
                continue
            if c in date_cols:
                continue  # raw date cols are not used directly (only engineered)
            if pd.api.types.is_numeric_dtype(df[c]):
                numeric_inferred.append(c)
            else:
                categorical_inferred.append(c)

    # Final lists to use
    numeric_cols = list(dict.fromkeys(numeric_declared + engineered + numeric_inferred))
    categorical_cols = list(dict.fromkeys(categorical_declared + categorical_inferred))

    # ---- 2.3 Prepare df_out for debugging/inspection ----
    keep_context = [c for c in [id_col, target_col] if c in df.columns]
    df_out = df[keep_context].copy() if keep_context else pd.DataFrame(index=df.index)

    # ---- 2.4 Fit/transform using the ColumnTransformer ----
    # We must align the ColumnTransformer's column selections before first fit.
    # Rebuild a shallow clone with the decided columns if needed.
    _bind_columns_to_transformer(transformer, numeric_cols, categorical_cols)

    feature_df = df[numeric_cols + categorical_cols].copy()
    if fit_transform:
        X = transformer.fit_transform(feature_df)
    else:
        X = transformer.transform(feature_df)

    # ---- 2.5 Target vector (if available) ----
    y = None
    if target_col in df.columns:
        # Accept numeric target only; coerce if needed
        y = pd.to_numeric(df[target_col], errors="coerce").to_numpy()

    # Ensure dense ndarray
    if hasattr(X, "toarray"):
        X = X.toarray()

    return X, y, df_out


# -----------------------
# Internal util functions
# -----------------------
def _engineered_numeric_names(feats_section: Dict[str, Any]) -> List[str]:
    """Return possible engineered numeric names based on config (for initial ColumnTransformer)."""
    date_cols = _as_list(feats_section.get("date_columns"))
    use_weekday = bool(feats_section.get("use_weekday", True))
    use_month   = bool(feats_section.get("use_month", True))
    use_weekend = bool(feats_section.get("use_weekend", True))

    names: List[str] = []
    for col in date_cols:
        if use_weekday:
            names.append(f"{col}_weekday")
        if use_month:
            names.append(f"{col}_month")
        if use_weekend:
            names.append(f"{col}_weekend")
    return names


def _bind_columns_to_transformer(
    transformer: ColumnTransformer,
    numeric_cols: List[str],
    categorical_cols: List[str],
) -> None:
    """
    Ensure the ColumnTransformer holds the decided column lists.
    This prevents mismatch between declared vs inferred columns across fit/transform.
    """
    new_transformers = []
    for name, trans, cols in transformer.transformers:
        if name == "num":
            new_transformers.append((name, trans, list(numeric_cols)))
        elif name == "cat":
            new_transformers.append((name, trans, list(categorical_cols)))
        else:
            new_transformers.append((name, trans, cols))
    transformer.transformers = new_transformers

# --------------------------------------------------------------------
# Backward-compat wrapper: some code may import ExpensePreprocessor
# This class wraps the functional API (build_preprocessor/make_Xy).
# --------------------------------------------------------------------
class ExpensePreprocessor:
    """
    Thin wrapper around the functional API so that legacy imports like
    `from src.data.preprocessor import ExpensePreprocessor` keep working.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        # Build a transformer now; it will be "bound" to actual columns on first fit.
        self.transformer = build_preprocessor(cfg)

    # Optional convenience: fit on a dataframe to "bind" the column lists
    def fit(self, df):
        # Fit the ColumnTransformer using the current df (feature inference inside)
        make_Xy(df, self.cfg, self.transformer, fit_transform=True)
        return self

    # Transform-only path (e.g., for prediction)
    def transform(self, df):
        # Returns (X, y, df_out) just like the functional API
        return make_Xy(df, self.cfg, self.transformer, fit_transform=False)

    # Static pass-throughs (for callers that used class methods)
    @staticmethod
    def build_preprocessor(cfg):
        return build_preprocessor(cfg)

    @staticmethod
    def make_Xy(df, cfg, transformer, fit_transform=False):
        return make_Xy(df, cfg, transformer, fit_transform=fit_transform)