import os
import csv
from collections import defaultdict
from datetime import date

import predici_spese

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Installare matplotlib: python -m pip install matplotlib")
    raise


def canonical_category(cat: str, desc: str = "") -> str:
    s = (cat or "").lower()
    d = (desc or "").lower()
    if "affitto" in s:
        return "Affitto"
    if "supermercato" in s or "spesa supermercato" in s:
        return "Supermercato"
    if "ristoranti" in s or "bar" in s:
        return "Ristoranti/Bar"
    if "trasporti" in s or "carburante" in s:
        return "Trasporti"
    if "utenze" in s:
        if "internet" in s or "fibra" in s:
            return "Utenze - Internet"
        if "luce" in s or "gas" in s:
            return "Utenze - Luce/Gas"
        if "acqua" in s:
            return "Utenze - Acqua"
        return "Utenze"
    if "intrattenimento" in s:
        return "Intrattenimento"
    if "sanit" in s or "assicur" in s:
        return "Sanità/Assicurazioni"
    if "commission" in s:
        return "Commissioni"
    if "rimbor" in s:
        return "Rimborsi"
    return "Varie"


def aggregate_expenses_by_category_monthly(rows: list):
    months_set = set()
    month_cat_sum = defaultdict(lambda: defaultdict(float))
    for r in rows:
        imp = r["importo"]
        tipo = r["tipo"]
        # consideriamo solo uscite (debiti / importi negativi)
        if imp < 0 or tipo == "debito":
            m = predici_spese.month_start(r["data"])  # date -> month start
            months_set.add(m)
            cat = canonical_category(r.get("categoria", ""), r.get("descrizione", ""))
            month_cat_sum[m][cat] += (-imp if imp < 0 else 0.0)
    months_sorted = sorted(months_set)

    # ordina le categorie per spesa totale decrescente
    total_by_cat = defaultdict(float)
    for m in months_sorted:
        for c, v in month_cat_sum[m].items():
            total_by_cat[c] += v
    categories_sorted = [c for c, _ in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True)]

    # costruisci matrice valori (len(months) x len(categories))
    values = {c: [month_cat_sum[m].get(c, 0.0) for m in months_sorted] for c in categories_sorted}

    return months_sorted, categories_sorted, values, total_by_cat


def write_monthly_pivot_csv(out_path: str, months: list, categories: list, values: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["anno_mese"] + categories + ["totale_spese"]
        w.writerow(header)
        for i, m in enumerate(months):
            row_vals = [values[c][i] for c in categories]
            total = sum(row_vals)
            w.writerow([f"{m.year}-{m.month:02d}"] + [f"{v:.2f}" for v in row_vals] + [f"{total:.2f}"])


def write_total_by_category_csv(out_path: str, total_by_cat: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["categoria", "spesa_totale"])
        for c, v in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True):
            w.writerow([c, f"{v:.2f}"])


def plot_stacked_monthly(out_path: str, months: list, categories: list, values: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs = list(range(len(months)))
    labels = [f"{m.year}-{m.month:02d}" for m in months]

    plt.figure(figsize=(11, 6))
    bottoms = [0.0] * len(xs)
    cmap = plt.cm.get_cmap("tab20", max(10, len(categories)))
    for idx, c in enumerate(categories):
        series = values[c]
        plt.bar(xs, series, bottom=bottoms, label=c, color=cmap(idx))
        bottoms = [b + s for b, s in zip(bottoms, series)]
    plt.xticks(xs, labels, rotation=45, ha="right")
    plt.ylabel("Spesa (€)")
    plt.title("Spese mensili per categoria (stacked)")
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()


def plot_pie_total(out_path: str, total_by_cat: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cats = [c for c, _ in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True)]
    vals = [total_by_cat[c] for c in cats]
    plt.figure(figsize=(8, 8))
    plt.pie(vals, labels=cats, autopct="%1.1f%%", startangle=90, counterclock=False)
    plt.title("Distribuzione totale spese per categoria")
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    estratto_path = os.path.join(base_dir, "data", "csv", "estratto_conto.csv")
    if not os.path.exists(estratto_path):
        print("CSV di estratto conto non trovato. Esegui prima genera_estratto_conto.py")
        return

    rows = predici_spese.load_transactions(estratto_path)
    months, categories, values, total_by_cat = aggregate_expenses_by_category_monthly(rows)

    # output CSV
    out_csv_monthly = os.path.join(base_dir, "data", "csv", "spese_per_categoria_mensile.csv")
    out_csv_total = os.path.join(base_dir, "data", "csv", "spese_per_categoria_totale.csv")
    write_monthly_pivot_csv(out_csv_monthly, months, categories, values)
    write_total_by_category_csv(out_csv_total, total_by_cat)

    # plot in data/plots
    out_plot_stack = os.path.join(base_dir, "data", "plots", "spese_per_categoria_mensile.png")
    out_plot_pie = os.path.join(base_dir, "data", "plots", "spese_per_categoria_totale.png")
    plot_stacked_monthly(out_plot_stack, months, categories, values)
    plot_pie_total(out_plot_pie, total_by_cat)

    print("Generati:")
    print("-", out_csv_monthly)
    print("-", out_csv_total)
    print("-", out_plot_stack)
    print("-", out_plot_pie)


if __name__ == "__main__":
    main()