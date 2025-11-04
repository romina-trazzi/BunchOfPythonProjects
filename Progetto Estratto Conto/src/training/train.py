# src/training/train.py

import argparse
import yaml
import os
from src.training.trainer import train_model


def load_config(config_path: str) -> dict:
    """Carica la configurazione YAML del progetto."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="CLI per addestrare il modello di classificazione spese personali"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Percorso al file CSV di input (es. data/raw/sample_data.csv)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Percorso al file di configurazione YAML (default: config.yaml)"
    )
    args = parser.parse_args()

    # Carica la configurazione
    config = load_config(args.config)
    print(f"Configurazione caricata da {args.config}")

    # Avvia il training
    print(f"Inizio training con dataset: {args.input}")
    train_model(input_path=args.input, config=config)

    print("✅ Training completato con successo!")


if __name__ == "__main__":
    main()
    