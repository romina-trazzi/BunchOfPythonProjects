import argparse
import os
import subprocess
from src.pipelines import pipeline

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def cmd_dashboard(args):
    # Avvia la dashboard esistente
    subprocess.run(["python", os.path.join(ROOT_DIR, "app.py")], check=True)


def main():
    parser = argparse.ArgumentParser(prog="predittore", description="CLI Predittore Spese")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run-all", help="Esegue pipeline completa").set_defaults(func=lambda a: pipeline.run_all())
    sub.add_parser("ingest", help="Genera estratto conto").set_defaults(func=lambda a: pipeline.run_generate())
    sub.add_parser("predict", help="Calcola previsione spese").set_defaults(func=lambda a: pipeline.run_predict())
    sub.add_parser("compare", help="Grafico comparativo").set_defaults(func=lambda a: pipeline.run_compare())
    sub.add_parser("categories", help="Analisi base per categorie").set_defaults(func=lambda a: pipeline.run_categories())
    sub.add_parser("summary", help="Riepilogo entrate/spese/saldo").set_defaults(func=lambda a: pipeline.run_summary())

    adv = sub.add_parser("advanced", help="Analisi avanzata categorie")
    adv.add_argument("--months", type=int, default=None, help="Ultimi N mesi")
    adv.add_argument("--include-entrate", action="store_true", help="Includi entrate")
    adv.set_defaults(func=lambda a: pipeline.run_advanced(months=a.months, include_entrate=a.include_entrate))

    sub.add_parser("dashboard", help="Avvia dashboard web").set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()