ChatBOT/
├── app.py                  # Flask app principale
├── requirements.txt
├── static/
│   ├── css/                # Bootstrap (opzionale se usi CDN)
│   └── js/                 # Script JS del chatbot
├── templates/
│   └── index.html          # Frontend
├── utils/
│   ├── finance_data.py     # Fetch dati da yfinance
│   ├── graph_generator.py  # Crea grafico PNG
│   └── pdf_generator.py    # Crea report PDF
└── output/
    ├── charts/             # Grafici salvati temporaneamente
    └── reports/            # PDF generati