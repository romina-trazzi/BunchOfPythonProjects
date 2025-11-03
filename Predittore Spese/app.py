import os
import glob
import subprocess
import json
import csv
import re
import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash

import genera_estratto_conto
import predici_spese
import grafico_comparativo
import analisi_categorie
import riepilogo_mensile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(BASE_DIR, "data", "plots")
CSV_DIR = os.path.join(BASE_DIR, "data", "csv")
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")

app = Flask(__name__)
app.secret_key = "predittore-spese-secret"


def ensure_dirs():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(CSV_DIR, exist_ok=True)


def load_alert_config():
    ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        cfg = {"alert_months": 3, "alert_tolerance": 0.2}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"alert_months": 3, "alert_tolerance": 0.2}


def save_alert_config(cfg):
    ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def list_plots():
    ensure_dirs()
    files = sorted([os.path.basename(p) for p in glob.glob(os.path.join(PLOTS_DIR, "*.png"))])
    return files


def run_safe(fn, label: str):
    try:
        fn()
        flash(f"OK: {label}", "success")
    except Exception as e:
        flash(f"Errore {label}: {e}", "error")


def compute_category_alerts():
    cfg = load_alert_config()
    pivot_path = os.path.join(CSV_DIR, "spese_per_categoria_mensile.csv")
    if not os.path.exists(pivot_path):
        return {"alerts": [], "missing": True, "months": cfg["alert_months"], "tolerance": cfg["alert_tolerance"], "latest": None}

    # Leggi CSV pivot (categorie per righe, mesi YYYY-MM per colonne)
    month_cols = []
    rows = []
    try:
        with open(pivot_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for fn in fieldnames:
                if re.fullmatch(r"\d{4}-\d{2}", fn or ""):
                    month_cols.append(fn)
            month_cols.sort()
            for row in reader:
                rows.append(row)
    except Exception as e:
        flash(f"Errore lettura CSV categorie: {e}", "error")
        return {"alerts": [], "missing": True, "months": cfg["alert_months"], "tolerance": cfg["alert_tolerance"], "latest": None}

    if not month_cols:
        return {"alerts": [], "missing": True, "months": cfg["alert_months"], "tolerance": cfg["alert_tolerance"], "latest": None}

    latest = month_cols[-1]
    months = max(1, int(cfg.get("alert_months", 3)))
    tolerance = float(cfg.get("alert_tolerance", 0.2))
    # Colonne precedenti al mese corrente
    prev_cols = month_cols[:-1]
    # Prendi al massimo gli ultimi N mesi precedenti
    prev_cols = prev_cols[-months:] if prev_cols else []

    def to_float(v):
        try:
            return float(str(v).replace(',', '.'))
        except Exception:
            return 0.0

    alerts = []
    for row in rows:
        cat = row.get("Categoria") or row.get("category") or row.get("Category") or "Senza categoria"
        current = to_float(row.get(latest))
        prev_vals = [to_float(row.get(c)) for c in prev_cols]
        prev_vals = [v for v in prev_vals if v is not None]
        if len(prev_vals) == 0:
            # Nessuna storia: salta alert finché non c'è baseline
            continue
        avg = sum(prev_vals) / len(prev_vals)
        threshold = avg * (1.0 + tolerance)
        if current > threshold and current > 0:
            alerts.append({
                "categoria": cat,
                "mese": latest,
                "spesa": round(current, 2),
                "media": round(avg, 2),
                "soglia": round(threshold, 2)
            })

    return {
        "alerts": alerts,
        "missing": False,
        "months": months,
        "tolerance": tolerance,
        "latest": latest
    }


@app.route("/")
def index():
    plots = list_plots()
    alerts_info = compute_category_alerts()
    return render_template("index.html", plots=plots, alerts_info=alerts_info)


@app.route("/plots/<path:filename>")
def serve_plot(filename: str):
    return send_from_directory(PLOTS_DIR, filename)


@app.route("/alerts_settings", methods=["POST"]) 
def alerts_settings():
    cfg = load_alert_config()
    months = request.form.get("alert_months")
    tolerance = request.form.get("alert_tolerance")
    changed = False
    if months:
        try:
            m = int(months)
            if m >= 1:
                cfg["alert_months"] = m
                changed = True
        except Exception:
            pass
    if tolerance:
        try:
            t = float(tolerance)
            if t >= 0:
                cfg["alert_tolerance"] = t
                changed = True
        except Exception:
            pass
    if changed:
        save_alert_config(cfg)
        flash("Impostazioni alert aggiornate", "success")
    else:
        flash("Impostazioni non valide", "error")
    return redirect(url_for("index"))


@app.route("/run_generate", methods=["POST"]) 
def run_generate():
    def _task():
        genera_estratto_conto.main()
    run_safe(_task, "Generazione estratto conto")
    return redirect(url_for("index"))


@app.route("/run_predict", methods=["POST"]) 
def run_predict():
    def _task():
        predici_spese.main()
    run_safe(_task, "Calcolo previsione")
    return redirect(url_for("index"))


@app.route("/run_compare", methods=["POST"]) 
def run_compare():
    def _task():
        grafico_comparativo.main()
    run_safe(_task, "Grafico comparativo")
    return redirect(url_for("index"))


@app.route("/run_categories", methods=["POST"]) 
def run_categories():
    def _task():
        analisi_categorie.main()
    run_safe(_task, "Analisi per categoria (base)")
    return redirect(url_for("index"))


@app.route("/run_summary", methods=["POST"]) 
def run_summary():
    def _task():
        riepilogo_mensile.main()
    run_safe(_task, "Riepilogo mensile entrate vs spese")
    return redirect(url_for("index"))


@app.route("/run_advanced", methods=["POST"]) 
def run_advanced():
    months = request.form.get("months")
    include_entrate = request.form.get("include_entrate") == "on"
    args = ["python", os.path.join(BASE_DIR, "analisi_categorie_avanzata.py")]
    if include_entrate:
        args.append("--include-entrate")
    if months:
        try:
            m = int(months)
            if m > 0:
                args += ["--months", str(m)]
        except Exception:
            pass
    try:
        subprocess.run(args, cwd=BASE_DIR, check=True)
        flash("OK: Analisi avanzata eseguita", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Errore analisi avanzata: {e}", "error")
    return redirect(url_for("index"))


@app.route("/run_all", methods=["POST"]) 
def run_all():
    def _task():
        genera_estratto_conto.main()
        predici_spese.main()
        grafico_comparativo.main()
        analisi_categorie.main()
        riepilogo_mensile.main()
    run_safe(_task, "Pipeline completa: dati, previsione, grafici")
    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_dirs()
    app.run(host="127.0.0.1", port=5000, debug=True)