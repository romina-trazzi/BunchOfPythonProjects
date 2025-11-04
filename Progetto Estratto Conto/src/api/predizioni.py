# src/api/predizioni.py
# ------------------------------------------------------------
# API FastAPI per training e predizione modello spese personali
# compatibile con frontend HTML
# ------------------------------------------------------------

from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io, os, joblib, base64
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

router = APIRouter(prefix="/v1", tags=["ml"])
MODEL_PATH = "models/latest.joblib"


# ------------------------------------------------------------
# TRAIN
# ------------------------------------------------------------
@router.post("/train/upload", summary="Upload CSV e addestra il modello")
async def train_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore nel caricamento CSV: {e}")

    expected = {"date", "amount", "category", "merchant", "day_of_week", "is_weekend", "month"}
    if not expected.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"Colonne mancanti. Attese: {sorted(list(expected))}")

    X = df.drop(columns=["category"])
    y = df["category"]

    categorical = ["merchant", "day_of_week"]
    numeric = ["amount", "is_weekend", "month"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", "passthrough", numeric),
        ]
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("clf", clf)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    report = classification_report(y_test, preds, output_dict=True)

    # Confusion matrix plot
    cm = confusion_matrix(y_test, preds, labels=clf.classes_)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=clf.classes_, yticklabels=clf.classes_)
    plt.xlabel("Predetto")
    plt.ylabel("Reale")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    os.makedirs("models", exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    return {
        "status": "ok",
        "message": "Training completato ✅",
        "model_path": MODEL_PATH,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "metrics": report,
        "plot_base64": img_b64,
    }


# ------------------------------------------------------------
# PREDICT
# ------------------------------------------------------------
@router.post("/predict/upload", summary="Upload CSV per predizione batch")
async def predict_upload(file: UploadFile = File(...)):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail=f"Model file not found: {MODEL_PATH}")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore nel caricamento CSV: {e}")

    expected = {"date", "amount", "merchant", "day_of_week", "is_weekend", "month"}
    missing = expected - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Colonne mancanti: {missing}")

    try:
        model = joblib.load(MODEL_PATH)
        preds = model.predict(df)
        df["predicted_category"] = preds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la predizione: {e}")

    return {
        "status": "ok",
        "message": "Predizione completata ✅",
        "rows": len(df),
        "preview": df.head(10).to_dict(orient="records"),
    }