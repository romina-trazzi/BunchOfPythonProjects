import os
import csv
from datetime import date

import predici_spese

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    print("Errore: matplotlib non installato. Installa con: python -m pip install matplotlib")
    raise


def parse_anno_mese(s: str) -> date:
    # formato atteso: YYYY-MM
    year, month = s.split("-")
    return date(int(year), int(month), 1)


def load_previsione(previsione_path: str) -> tuple[date, float, float]:
    if not os.path.exists(previsione_path):
        raise FileNotFoundError("File previsione non trovato: " + previsione_path)
    with open(previsione_path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            # usa la prima riga di dati
            next_month = parse_anno_mese(row.get("anno_mese") or row.get("Anno_Mese"))
            y_pred = float(row.get("spesa_prevista") or row.get("Spesa_Prevista"))
            r2 = float(row.get("r2") or row.get("R2", 0.0))
            return next_month, y_pred, r2
    raise ValueError("Nessuna riga di previsione trovata nel CSV")


def crea_grafico(estratto_path: str, previsione_path: str, out_path: str) -> str:
    # carica storico
    rows = predici_spese.load_transactions(estratto_path)
    months, y = predici_spese.aggregate_monthly_expenses(rows)
    if not months:
        raise ValueError("Nessuna spesa mensile trovata nello storico")

    # carica previsione
    next_month, y_pred, r2 = load_previsione(previsione_path)

    # asse X numerico con etichette mensili
    xs = list(range(len(months)))
    x_next = len(xs)
    labels = [f"{m.year}-{m.month:02d}" for m in months] + [f"{next_month.year}-{next_month.month:02d}"]

    # grafico
    plt.figure(figsize=(10, 6))
    plt.plot(xs, y, marker="o", label="Storico spese mensili")
    plt.scatter([x_next], [y_pred], color="red", marker="*", s=160, label="Spesa prevista")
    # linea tratteggiata che collega ultimo punto alla previsione
    plt.plot([xs[-1], x_next], [y[-1], y_pred], "r--", alpha=0.7)

    plt.xticks(xs + [x_next], labels, rotation=45, ha="right")
    plt.ylabel("Spesa (€)")
    plt.title(f"Confronto spese: storico vs previsione (R^2={r2:.3f})")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    estratto_path = os.path.join(base_dir, "data", "csv", "estratto_conto.csv")
    previsione_path = os.path.join(base_dir, "data", "csv", "previsione_spese.csv")
    out_path = os.path.join(base_dir, "data", "plots", "grafico_spese_comparativo.png")

    if not os.path.exists(estratto_path):
        print("CSV di estratto conto non trovato. Esegui prima genera_estratto_conto.py")
        return
    if not os.path.exists(previsione_path):
        print("CSV di previsione non trovato. Esegui prima predici_spese.py")
        return

    out = crea_grafico(estratto_path, previsione_path, out_path)
    print("Grafico generato:", out)


if __name__ == "__main__":
    main()