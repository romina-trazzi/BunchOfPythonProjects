import os
import csv
import argparse
from collections import defaultdict
from datetime import date

import predici_spese

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Installare matplotlib: python -m pip install matplotlib")
    raise


def parse_anno_mese(s: str) -> date:
    year, month = s.split("-")
    return date(int(year), int(month), 1)


def canonical_category(cat: str, desc: str = "") -> str:
    s = (cat or "").lower()
    d = (desc or "").lower()
    if "stipendio" in s or "stipendio" in d:
        return "Stipendio"
    if "affitto" in s or "affitto" in d:
        return "Affitto"
    if "supermercato" in s or "spesa supermercato" in s:
        return "Supermercato"
    if "ristoranti" in s or "ristorante" in d or "bar" in s or "pizzeria" in d:
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
    if "rimbor" in s or "rimbor" in d:
        return "Rimborsi"
    return "Varie"


def aggregate_by_category_monthly(rows: list, include_expenses: bool = True) -> tuple[list, list, dict, dict]:
    months_set = set()
    month_cat_sum = defaultdict(lambda: defaultdict(float))
    for r in rows:
        imp = r["importo"]
        tipo = r["tipo"]
        is_expense = (imp < 0 or tipo == "debito")
        is_income = (imp > 0 or tipo == "credito")
        if include_expenses and is_expense:
            m = predici_spese.month_start(r["data"])  # date -> month start
            months_set.add(m)
            cat = canonical_category(r.get("categoria", ""), r.get("descrizione", ""))
            month_cat_sum[m][cat] += (-imp if imp < 0 else 0.0)
        if not include_expenses and is_income:
            m = predici_spese.month_start(r["data"])  # date -> month start
            months_set.add(m)
            cat = canonical_category(r.get("categoria", ""), r.get("descrizione", ""))
            month_cat_sum[m][cat] += (imp if imp > 0 else 0.0)
    months_sorted = sorted(months_set)

    total_by_cat = defaultdict(float)
    for m in months_sorted:
        for c, v in month_cat_sum[m].items():
            total_by_cat[c] += v
    categories_sorted = [c for c, _ in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True)]

    values = {c: [month_cat_sum[m].get(c, 0.0) for m in months_sorted] for c in categories_sorted}
    return months_sorted, categories_sorted, values, total_by_cat


def write_monthly_pivot_csv(out_path: str, months: list, categories: list, values: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["anno_mese"] + categories + ["totale"]
        w.writerow(header)
        for i, m in enumerate(months):
            row_vals = [values[c][i] for c in categories]
            total = sum(row_vals)
            w.writerow([f"{m.year}-{m.month:02d}"] + [f"{v:.2f}" for v in row_vals] + [f"{total:.2f}"])


def write_total_by_category_csv(out_path: str, total_by_cat: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["categoria", "totale"])
        for c, v in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True):
            w.writerow([c, f"{v:.2f}"])


def plot_stacked_monthly(out_path: str, months: list, categories: list, values: dict, title: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs = list(range(len(months)))
    labels = [f"{m.year}-{m.month:02d}" for m in months]

    plt.figure(figsize=(11, 6))
    bottoms = [0.0] * len(xs)
    cmap = plt.get_cmap("tab20", max(10, len(categories)))
    for idx, c in enumerate(categories):
        series = values[c]
        plt.bar(xs, series, bottom=bottoms, label=c, color=cmap(idx))
        bottoms = [b + s for b, s in zip(bottoms, series)]
    plt.xticks(xs, labels, rotation=45, ha="right")
    plt.ylabel("€")
    plt.title(title)
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()


def plot_pie_total(out_path: str, total_by_cat: dict, title: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cats = [c for c, _ in sorted(total_by_cat.items(), key=lambda kv: kv[1], reverse=True)]
    vals = [total_by_cat[c] for c in cats]
    plt.figure(figsize=(8, 8))
    plt.pie(vals, labels=cats, autopct="%1.1f%%", startangle=90, counterclock=False)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Analisi spese/entrate per categoria, con filtri periodo")
    parser.add_argument("--start", type=str, default=None, help="Inizio periodo in formato YYYY-MM")
    parser.add_argument("--end", type=str, default=None, help="Fine periodo in formato YYYY-MM (incluso)")
    parser.add_argument("--months", type=int, default=None, help="Ultimi N mesi da includere")
    parser.add_argument("--include-entrate", action="store_true", help="Genera anche breakdown delle entrate")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    estratto_path = os.path.join(base_dir, "data", "csv", "estratto_conto.csv")
    if not os.path.exists(estratto_path):
        print("CSV di estratto conto non trovato. Esegui prima genera_estratto_conto.py")
        return

    rows = predici_spese.load_transactions(estratto_path)

    # filtro per periodo
    if args.start:
        start_m = parse_anno_mese(args.start)
    else:
        start_m = None
    if args.end:
        end_m = parse_anno_mese(args.end)
    else:
        end_m = None

    # se --months è fornito, sovrascrive start/end in base agli ultimi N mesi
    if args.months is not None and args.months > 0:
        # trova l'ultimo mese presente nei dati
        all_months = sorted({predici_spese.month_start(r["data"]) for r in rows})
        if all_months:
            end_m = all_months[-1]
            # calcola start_m come end_m - (months-1)
            start_m = predici_spese.add_months(end_m, -(args.months - 1))

    def in_period(dt: date) -> bool:
        m = predici_spese.month_start(dt)
        if start_m and m < start_m:
            return False
        if end_m and m > end_m:
            return False
        return True

    rows_f = [r for r in rows if in_period(r["data"])]

    # spese
    months_s, categories_s, values_s, total_by_cat_s = aggregate_by_category_monthly(rows_f, include_expenses=True)
    out_csv_monthly_s = os.path.join(base_dir, "data", "csv", "spese_per_categoria_mensile.csv")
    out_csv_total_s = os.path.join(base_dir, "data", "csv", "spese_per_categoria_totale.csv")
    write_monthly_pivot_csv(out_csv_monthly_s, months_s, categories_s, values_s)
    write_total_by_category_csv(out_csv_total_s, total_by_cat_s)

    out_plot_stack_s = os.path.join(base_dir, "data", "plots", "spese_per_categoria_mensile.png")
    out_plot_pie_s = os.path.join(base_dir, "data", "plots", "spese_per_categoria_totale.png")
    plot_stacked_monthly(out_plot_stack_s, months_s, categories_s, values_s, "Spese mensili per categoria (stacked)")
    plot_pie_total(out_plot_pie_s, total_by_cat_s, "Distribuzione totale spese per categoria")

    # entrate
    if args.include_entrate:
        months_e, categories_e, values_e, total_by_cat_e = aggregate_by_category_monthly(rows_f, include_expenses=False)
        out_csv_monthly_e = os.path.join(base_dir, "data", "csv", "entrate_per_categoria_mensile.csv")
        out_csv_total_e = os.path.join(base_dir, "data", "csv", "entrate_per_categoria_totale.csv")
        write_monthly_pivot_csv(out_csv_monthly_e, months_e, categories_e, values_e)
        write_total_by_category_csv(out_csv_total_e, total_by_cat_e)

        out_plot_stack_e = os.path.join(base_dir, "data", "plots", "entrate_per_categoria_mensile.png")
        out_plot_pie_e = os.path.join(base_dir, "data", "plots", "entrate_per_categoria_totale.png")
        plot_stacked_monthly(out_plot_stack_e, months_e, categories_e, values_e, "Entrate mensili per categoria (stacked)")
        plot_pie_total(out_plot_pie_e, total_by_cat_e, "Distribuzione totale entrate per categoria")

    print("Generati:")
    print("-", out_csv_monthly_s)
    print("-", out_csv_total_s)
    print("-", out_plot_stack_s)
    print("-", out_plot_pie_s)
    if args.include_entrate:
        print("-", out_csv_monthly_e)
        print("-", out_csv_total_e)
        print("-", out_plot_stack_e)
        print("-", out_plot_pie_e)


if __name__ == "__main__":
    main()