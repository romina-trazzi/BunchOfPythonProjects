import os
import subprocess

# Reuse existing scripts to keep backward compatibility
import genera_estratto_conto
import predici_spese
import grafico_comparativo
import analisi_categorie
import riepilogo_mensile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))


def run_generate():
    genera_estratto_conto.main()


def run_predict():
    predici_spese.main()


def run_compare():
    grafico_comparativo.main()


def run_categories():
    analisi_categorie.main()


def run_summary():
    riepilogo_mensile.main()


def run_advanced(months: int | None = None, include_entrate: bool = False):
    args = ["python", os.path.join(ROOT_DIR, "analisi_categorie_avanzata.py")]
    if include_entrate:
        args.append("--include-entrate")
    if months and months > 0:
        args += ["--months", str(months)]
    subprocess.run(args, cwd=ROOT_DIR, check=True)


def run_all():
    run_generate()
    run_predict()
    run_compare()
    run_categories()
    run_summary()