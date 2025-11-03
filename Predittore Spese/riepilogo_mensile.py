import os
import csv
from datetime import date

import predici_spese

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Installare matplotlib: python -m pip install matplotlib")
    raise


def aggregate_monthly(rows: list):
    monthly = {}
    for r in rows:
        m = predici_spese.month_start(r["data"])  # primo giorno del mese
        imp = r["importo"]
        tipo = r["tipo"]
        if m not in monthly:
            monthly[m] = {"entrate": 0.0, "spese": 0.0}
        if imp > 0 or tipo == "credito":
            monthly[m]["entrate"] += (imp if imp > 0 else 0.0)
        if imp < 0 or tipo == "debito":
            monthly[m]["spese"] += (-imp if imp < 0 else 0.0)
    months_sorted = sorted(monthly.keys())
    entrate = [monthly[m]["entrate"] for m in months_sorted]
    spese = [monthly[m]["spese"] for m in months_sorted]
    saldo = [e - s for e, s in zip(entrate, spese)]
    return months_sorted, entrate, spese, saldo


def write_csv(months: list, entrate: list, spese: list, saldo: list, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anno_mese", "entrate", "spese", "saldo"])
        for i, m in enumerate(months):
            w.writerow([
                f"{m.year}-{m.month:02d}",
                f"{entrate[i]:.2f}",
                f"{spese[i]:.2f}",
                f"{saldo[i]:.2f}",
            ])
    return out_path


def plot_entrate_spese_saldo(months: list, entrate: list, spese: list, saldo: list, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    labels = [f"{m.year}-{m.month:02d}" for m in months]
    xs = list(range(len(months)))
    width = 0.42

    plt.figure(figsize=(11, 6))
    # Barre affiancate per entrate e spese
    plt.bar([x - width/2 for x in xs], entrate, width=width, label="Entrate", color="tab:green")
    plt.bar([x + width/2 for x in xs], spese, width=width, label="Spese", color="tab:red")
    # Linea per saldo centrata sui tick
    plt.plot(xs, saldo, color="tab:blue", marker="o", label="Saldo")

    plt.xticks(xs, labels, rotation=45, ha="right")
    plt.ylabel("€")
    plt.title("Entrate vs Spese con Saldo (mensile)")
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    in_path = os.path.join(base_dir, "data", "csv", "estratto_conto.csv")
    if not os.path.exists(in_path):
        print("CSV di estratto conto non trovato. Esegui prima genera_estratto_conto.py")
        return

    rows = predici_spese.load_transactions(in_path)
    months, entrate, spese, saldo = aggregate_monthly(rows)

    out_csv = os.path.join(base_dir, "data", "csv", "riepilogo_mensile.csv")
    out_png = os.path.join(base_dir, "data", "plots", "entrate_vs_spese_saldo_mensile.png")

    write_csv(months, entrate, spese, saldo, out_csv)
    plot_entrate_spese_saldo(months, entrate, spese, saldo, out_png)

    print("Generati:")
    print("-", out_csv)
    print("-", out_png)


if __name__ == "__main__":
    main()