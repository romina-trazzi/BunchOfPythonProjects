# Servizio di Rilevamento Malattie della Pelle

Questo servizio REST utilizza LangChain e FastAPI per fornire un'interfaccia al servizio di rilevamento malattie della pelle di RapidAPI.

## Installazione

1. Installare le dipendenze:

```bash
pip install -r requirements.txt
```

## Avvio del servizio

```bash
python main.py
```

Il servizio sarà disponibile all'indirizzo http://localhost:8000

## Utilizzo

### Endpoint disponibili

- `GET /`: Informazioni sul servizio
- `POST /detect-skin-disease/`: Analizza un'immagine per rilevare malattie della pelle

### Esempio di richiesta

```bash
curl -X POST "http://localhost:8000/detect-skin-disease/" \
     -H "Content-Type: application/json" \
     -d '{"image_url": "https://example.com/image.jpg"}'
```

## Documentazione API

La documentazione interattiva è disponibile all'indirizzo:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)