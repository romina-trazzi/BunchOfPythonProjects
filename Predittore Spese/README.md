# Predittore Spese — Boilerplate Architetturale

Questo boilerplate organizza il progetto per analisi di flussi Entrate/Spese in contesti diversi (privato, azienda, associazione), mantenendo compatibilità con gli script esistenti.

## Struttura

```
Predittore Spese/
├── src/
│   ├── domain/
│   │   ├── __init__.py
│   │   └── models.py               # Modelli base (Transaction, MonthlyAggregate, AlertItem)
│   ├── data/
│   │   ├── __init__.py
│   │   └── repository.py           # IO CSV: lettura transazioni, scrittura tabelle
│   ├── services/
│   │   ├── __init__.py
│   │   ├── categorization.py       # Regole di categorizzazione pluggable
│   │   ├── analytics.py            # Aggregazioni mensili e pivot per categoria
│   │   ├── alerts.py               # Calcolo alert da pivot CSV
│   │   └── plots.py                # Funzioni di plotting (backend Agg)
│   └── pipelines/
│       ├── __init__.py
│       └── pipeline.py             # Orchestratori che riusano gli script attuali
├── cli.py                          # CLI con subcomandi per le pipeline e la dashboard
├── app.py                          # Dashboard Flask attuale (compatibile)
├── config/
│   ├── base.json                   # Impostazioni base del progetto
│   └── categories_rules.json       # Regole categoria basate su keyword (facoltativo)
├── profiles/
│   └── default/
│       └── settings.json           # Esempio profilo (budget, soglie, ecc.)
├── data/
│   ├── csv/                        # Dataset e output tabellari
│   └── plots/                      # Grafici PNG
└── README.md
```

## Principi Architetturali
- **Separazione dei ruoli**: dominio, dati (IO), servizi (logiche), pipeline (orchestrazione), UI web.
- **Compatibilità**: gli script esistenti restano usabili; i servizi modulari permettono estensioni.
- **Configurabilità**: impostazioni generali in `config/`, varianti per contesti in `profiles/`.
- **Portabilità**: CLI standard con `argparse` per automatizzare flussi.

## CLI
Eseguire:
```
python cli.py --help
```
Subcomandi principali:
- `run-all` — pipeline completa
- `ingest` — genera estratto conto
- `predict` — previsione spese
- `compare` — grafico comparativo
- `categories` — analisi base per categoria
- `advanced --months N [--include-entrate]` — analisi avanzata
- `summary` — riepilogo entrate/spese/saldo
- `dashboard` — avvia la dashboard web

## Configurazione
- `config/base.json` — directory dati, soglie alert, ecc.
- `config/categories_rules.json` — mappa `{ "needle": "Categoria" }` per la categorizzazione.
- `profiles/default/settings.json` — esempio di profilo (budget per categoria, override soglie).

## Estensioni consigliate
- **Multi-profili**: parametri CLI `--profile` per usare config specifiche.
- **Budget per categoria**: alert aggiuntivi quando la spesa mensile supera il budget.
- **Integrazione DB**: sostituire CSV con DB (SQLite/PostgreSQL) via repository.
- **Notifiche**: email/Telegram per superamenti soglia.
- **ETL**: pipeline ingestion per import da ERP/gestionali, normalizzazione e deduplica.

## Note
- Il backend di Matplotlib è impostato su `Agg` nei moduli di plotting e nel server per evitare dipendenze grafiche (Tkinter).
- Gli script preesistenti sono riusati dagli orchestratori; la migrazione graduale delle logiche nei servizi è supportata.