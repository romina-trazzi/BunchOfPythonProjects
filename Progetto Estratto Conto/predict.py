# src/predictions/predict.py
# ------------------------------------------------------------
# CLI per generare predizioni con il modello classificatore
# ------------------------------------------------------------
import argparse
import pandas as pd
from pathlib import Path
import joblib

def main(args):
    print("=" * 60)
    print(" @ EXPENSE CLASSIFIER - Prediction")
    print("=" * 60)

    # Carica modello
    print(f"\n📦 Caricamento modello da {args.model}...")
    model = joblib.load(args.model)

    # Carica nuovi dati
    print(f"📥 Caricamento dati da {args.input}...")
    df = pd.read_csv(args.input)

    expected = {"date", "amount", "merchant", "day_of_week", "is_weekend", "month"}
    if not expected.issubset(df.columns):
        raise SystemExit(f"❌ Colonne mancanti. Attese: {sorted(list(expected))}")

    # Predizioni
    print("\n🤖 Generazione predizioni...")
    preds = model.predict(df)
    df["predicted_category"] = preds

    # Riepilogo
    print("\n📊 Distribuzione categorie predette:")
    print(df["predicted_category"].value_counts())

    # Salvataggio
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\n💾 Predizioni salvate in {out_path}")

    # (Opzionale) semplice verifica qualitativa
    print("\n🔍 Esempio prime righe:")
    print(df.head(5).to_string(index=False))
    print("\n🏁 Fine predizione.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predizione categorie spesa")
    parser.add_argument("--input", required=True, help="CSV di input con transazioni")
    parser.add_argument("--output", default="data/processed/predictions.csv", help="Percorso file di output")
    parser.add_argument("--model", default="models/latest.joblib", help="Percorso file modello salvato")
    args = parser.parse_args()
    main(args)