# src/api/predizioni.py
# ---------------------
# Purpose:
#   ML API via FastAPI with two styles of endpoints:
#     - JSON/Query based:
#         POST /v1/train      -> optional input_csv path
#         POST /v1/predict    -> optional input_csv/output_csv paths
#     - Multipart upload:
#         POST /v1/train/upload    -> upload CSV file
#         POST /v1/predict/upload  -> upload CSV file
#
# Behavior:
#   - Reads config/default.yaml
#   - Uses ExpenseRegressor (preprocessor + estimator)
#   - Splits data according to config.data train/val/test ratios
#   - Saves model and metrics; returns a concise JSON with paths and previews
#
# Notes:
#   - Upload endpoints save the incoming CSV under a configurable uploads dir:
#       cfg.data.uploads_dir  (if present)
#     otherwise fallback:
#       {cfg.data.processed_path}/uploads
#
#   - Keep endpoints lightweight for Swagger demo & simple frontend integration.

from __future__ import annotations

from typing import Any, Dict, Optional, List
from pathlib import Path
import shutil

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from yaml import safe_load
from sklearn.model_selection import train_test_split

from src.models.expense_regressor import ExpenseRegressor

router = APIRouter(prefix="/v1", tags=["ml"])


def _load_cfg() -> Dict[str, Any]:
    cfg_path = Path("config/default.yaml")
    if not cfg_path.exists():
        raise HTTPException(status_code=500, detail="config/default.yaml not found")
    with cfg_path.open("r", encoding="utf-8") as f:
        return safe_load(f)


def _ensure_dirs(cfg: Dict[str, Any]) -> Dict[str, Path]:
    data_dirs = {
        "processed": Path(cfg["data"]["processed_path"]),
        "models": Path(cfg["data"]["model_dir"]),
        "logs": Path(cfg["data"]["logs_dir"]),
    }
    # uploads dir: config override or default under processed/uploads
    uploads_dir = Path(
        cfg["data"].get("uploads_dir", (data_dirs["processed"] / "uploads"))
    )
    for p in [*data_dirs.values(), uploads_dir]:
        p.mkdir(parents=True, exist_ok=True)
    return {"uploads": uploads_dir, **data_dirs}


def _save_upload(uploads_dir: Path, uploaded: UploadFile, target_name: Optional[str] = None) -> Path:
    """
    Persist the uploaded file to uploads_dir. Returns the saved path.
    """
    suffix = ""
    # Try to preserve extension if any
    if uploaded.filename and "." in uploaded.filename:
        suffix = "." + uploaded.filename.split(".")[-1].lower()

    name = target_name or (uploaded.filename or "uploaded")
    if not name.lower().endswith(suffix) and suffix:
        name = f"{Path(name).stem}{suffix}"

    save_path = uploads_dir / name
    with save_path.open("wb") as out:
        shutil.copyfileobj(uploaded.file, out)
    return save_path


@router.post("/train", summary="Train model from default.yaml or provided CSV path")
def train(input_csv: Optional[str] = None) -> Dict[str, Any]:
    """
    Train the regressor using the CSV in config (or an override path in input_csv).
    Returns metrics and where the model/metrics were saved.
    """
    cfg = _load_cfg()
    dirs = _ensure_dirs(cfg)

    # Resolve paths
    raw_csv = Path(input_csv or cfg["data"]["raw_path"])
    if not raw_csv.exists():
        raise HTTPException(status_code=400, detail=f"Input CSV not found: {raw_csv}")

    model_path = Path(cfg["training"]["model_save_path"])
    metrics_path = Path(cfg["training"]["metrics_path"])

    # Load data
    df = pd.read_csv(raw_csv)

    # Split according to config.data ratios (train vs temp, then temp -> val/test)
    tr, va, te = cfg["data"]["train_split"], cfg["data"]["val_split"], cfg["data"]["test_split"]
    if abs((tr + va + te) - 1.0) > 1e-6:
        raise HTTPException(status_code=400, detail="train/val/test splits must sum to 1.0")

    df_train, df_tmp = train_test_split(df, test_size=(1 - tr), random_state=42, shuffle=True)
    if (va + te) == 0:
        df_val, df_test = pd.DataFrame(columns=df.columns), pd.DataFrame(columns=df.columns)
    else:
        rel_test = te / (va + te)
        df_val, df_test = train_test_split(df_tmp, test_size=rel_test, random_state=42, shuffle=True)

    # Train
    model = ExpenseRegressor(cfg).fit(df_train)

    # Evaluate on test (if present)
    if not df_test.empty and cfg["features"]["target_column"] in df_test.columns:
        pred_df = model.predict(df_test, return_df=True)
        y_true = pred_df["y_true"].to_numpy()
        y_pred = pred_df["y_pred"].to_numpy()
        metrics = model.regression_metrics(y_true, y_pred)
    else:
        metrics = {"mae": None, "rmse": None, "r2": None}

    # Persist
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    pd.Series(metrics).to_json(metrics_path, force_ascii=False)

    # Preview
    preview_cols = ["id_movimento", "data_movimento", "categoria", "sottocategoria"]
    train_preview = df_train.head(5)[[c for c in preview_cols if c in df_train.columns]].to_dict(orient="records")

    return {
        "status": "ok",
        "mode": "path",
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "metrics": metrics,
        "train_rows": int(len(df_train)),
        "val_rows": int(len(df_val)),
        "test_rows": int(len(df_test)),
        "train_preview": train_preview,
    }


@router.post("/train/upload", summary="Upload CSV and train")
async def train_upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a CSV and train the model on it.
    """
    cfg = _load_cfg()
    dirs = _ensure_dirs(cfg)
    saved = _save_upload(dirs["uploads"], file, target_name="train.csv")
    # Reuse the train() logic with the saved path
    return train(input_csv=str(saved))


@router.post("/predict", summary="Batch predict from default.yaml or provided CSV path")
def predict(
    input_csv: Optional[str] = None,
    output_csv: Optional[str] = None,
    limit_preview: int = 10
) -> Dict[str, Any]:
    """
    Load the trained model and score a CSV (default from config).
    Writes predictions to config.prediction.output_path (or override).
    Returns a small preview of predictions.
    """
    cfg = _load_cfg()
    dirs = _ensure_dirs(cfg)

    # Resolve paths
    model_path = Path(cfg["prediction"]["model_path"])
    if not model_path.exists():
        raise HTTPException(status_code=400, detail=f"Model file not found: {model_path}")

    in_path = Path(input_csv or cfg["prediction"]["input_path"])
    out_path = Path(output_csv or cfg["prediction"]["output_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise HTTPException(status_code=400, detail=f"Input CSV not found: {in_path}")

    # Load model and data
    model = ExpenseRegressor.load(str(model_path), cfg)
    df = pd.read_csv(in_path)

    # Predict
    pred_df = model.predict(df, return_df=True)

    # Select output columns
    out_cols: List[str] = cfg["prediction"].get("output_columns") or []
    if out_cols:
        keep = [c for c in out_cols if c in pred_df.columns]
        out = pred_df[keep]
    else:
        out = pred_df

    # Write and preview
    out.to_csv(out_path, index=False)
    preview = out.head(limit_preview).to_dict(orient="records")

    return {
        "status": "ok",
        "mode": "path",
        "input_csv": str(in_path),
        "output_csv": str(out_path),
        "preview": preview,
        "rows": int(len(out)),
    }


@router.post("/predict/upload", summary="Upload CSV and batch predict")
async def predict_upload(
    file: UploadFile = File(...),
    limit_preview: int = 10
) -> Dict[str, Any]:
    """
    Upload a CSV, run predictions, and return a preview.
    The output file will be written under config.prediction.output_path.
    """
    cfg = _load_cfg()
    dirs = _ensure_dirs(cfg)
    saved = _save_upload(dirs["uploads"], file, target_name="predict.csv")
    # Reuse the predict() logic with the saved path
    return predict(input_csv=str(saved), output_csv=None, limit_preview=limit_preview)
