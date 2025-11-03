# src/training/trainer.py
# -----------------------
# Purpose (English):
#   Centralize the model training/evaluation logic so it can be reused by:
#     - REST layer (FastAPI routers)
#     - CLI scripts (e.g., src/training/train.py)
#     - Notebooks or batch jobs
#
# What it does:
#   - load_cfg(): read config/default.yaml
#   - ensure_dirs(): create data/model/logs folders declared in the config
#   - split_df(): split DataFrame into train/val/test following ratios in config
#   - train_and_eval(): fit ExpenseRegressor, compute metrics on test, return artifacts
#   - save_artifacts(): persist model and metrics to disk
#
# Notes:
#   - This module DOES NOT depend on any web framework.
#   - It reuses the ExpenseRegressor wrapper, which internally uses the tabular preprocessor.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
from yaml import safe_load
from sklearn.model_selection import train_test_split

from src.models.expense_regressor import ExpenseRegressor


# -----------------------------
# Config helpers
# -----------------------------
def load_cfg(cfg_path: str = "config/default.yaml") -> Dict[str, Any]:
    p = Path(cfg_path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return safe_load(f)


def ensure_dirs(cfg: Dict[str, Any]) -> None:
    """Create data/model/logs directories declared in config, if missing."""
    # data section
    data_sec = cfg.get("data", {})
    for key in ("processed_path", "model_dir", "logs_dir"):
        val = data_sec.get(key)
        if val:
            Path(val).mkdir(parents=True, exist_ok=True)
    # explicit training/prediction artifact parents
    train_model = cfg.get("training", {}).get("model_save_path")
    metrics_path = cfg.get("training", {}).get("metrics_path")
    pred_out = cfg.get("prediction", {}).get("output_path")
    for pth in (train_model, metrics_path, pred_out):
        if pth:
            Path(pth).parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Data splitting
# -----------------------------
def split_df(df: pd.DataFrame, cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into train/val/test following ratios in cfg['data']."""
    data_sec = cfg.get("data", {})
    tr = float(data_sec.get("train_split", 0.7))
    va = float(data_sec.get("val_split", 0.15))
    te = float(data_sec.get("test_split", 0.15))

    if abs((tr + va + te) - 1.0) > 1e-6:
        raise ValueError("train/val/test splits must sum to 1.0")

    df_train, df_tmp = train_test_split(df, test_size=(1 - tr), random_state=cfg.get("training", {}).get("random_state", 42), shuffle=True)
    if (va + te) == 0:
        return df_train, pd.DataFrame(columns=df.columns), pd.DataFrame(columns=df.columns)

    rel_test = te / (va + te)
    df_val, df_test = train_test_split(df_tmp, test_size=rel_test, random_state=cfg.get("training", {}).get("random_state", 42), shuffle=True)
    return df_train, df_val, df_test


# -----------------------------
# Train & Evaluate
# -----------------------------
def train_and_eval(df: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fit model on train, evaluate on test.
    Returns a dict with model object, metrics, and small previews.
    """
    ensure_dirs(cfg)

    df_train, df_val, df_test = split_df(df, cfg)

    # Fit
    model = ExpenseRegressor(cfg).fit(df_train)

    # Evaluate on test (if target available)
    feats = cfg.get("features", {}) or {}
    target_col = feats.get("target_column", "importo")

    if not df_test.empty and target_col in df_test.columns:
        pred_df = model.predict(df_test, return_df=True)
        y_true = pred_df.get("y_true")
        y_pred = pred_df.get("y_pred")
        if y_true is not None and y_pred is not None:
            y_true = y_true.to_numpy()
            y_pred = y_pred.to_numpy()
            metrics = model.regression_metrics(y_true, y_pred)
        else:
            metrics = {"mae": None, "rmse": None, "r2": None}
    else:
        metrics = {"mae": None, "rmse": None, "r2": None}

    # Small training preview for logging/UX
    preview_cols = ["id_movimento", "data_movimento", "categoria", "sottocategoria"]
    train_preview = df_train.head(5)[[c for c in preview_cols if c in df_train.columns]].to_dict(orient="records")

    return {
        "model": model,
        "metrics": metrics,
        "splits": {
            "train_rows": int(len(df_train)),
            "val_rows": int(len(df_val)),
            "test_rows": int(len(df_test)),
        },
        "train_preview": train_preview,
    }


# -----------------------------
# Persistence helpers
# -----------------------------
def save_artifacts(art: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, str]:
    """
    Save model and metrics to disk using paths from config.
    Returns dict with saved paths.
    """
    model = art["model"]
    metrics = art["metrics"]

    model_path = Path(cfg["training"]["model_save_path"])
    metrics_path = Path(cfg["training"]["metrics_path"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    # Save model
    model.save(str(model_path))

    # Save metrics (JSON)
    pd.Series(metrics).to_json(metrics_path, force_ascii=False)

    return {
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
    }