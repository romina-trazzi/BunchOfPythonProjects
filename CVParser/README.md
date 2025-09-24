# 📄 CV Parser — Minimal & Modular

Benvenuta/o! Questo progetto espone una **piccola API** per estrarre e normalizzare i dati principali da un **CV in PDF**.

> 🎯 Obiettivi: codice **semplice**, **commentato**, con **funzioni a singola responsabilità** e **gestione errori** chiara.

---

## 🚀 Funzionamento (in 10 secondi)

1. **Avvio del frontend in React**

Dopo essere entrato nella cartella del frontend con:

```bash
cd cv-parser-frontend
```

Per sbloccare gli script in questa sessione:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Per aprire la porta 5173 e avviare il server frontend Vite:

```bash
npm run dev
```

2. **Avvio server**

Attiva il virtual venv:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```bash
.\venv\Scripts\Activate.ps1
```

Installa le dipendenze del progetto: 

```bash
pip install -r requirements.txt
```
Apre la porta del server uvicorn:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 
```

## 🧱 Struttura del progetto

.
├─ main.py            # Avvio FastAPI (minimale)
├─ extractors.py      # Estrazione testo: PyMuPDF (locale) o OCR.space (REST)
├─ parsers.py         # Parsing: sezioni, nome/cognome, lingue, esperienze, istruzione
├─ normalizers.py     # Normalizzazione nello schema target + sanitizzazione
├─ scoring.py         # Calcolo % di completamento (presence-based)
└─ utils.py           # Utility comuni (stringhe, date, telefono, name inference)


Ogni file contiene funzioni con uno scopo preciso.
Le funzioni cruciali hanno docstring + commenti per chi è agli inizi.

## 📦 Requisiti

- Python 3.10+

- Librerie Consigliate (per mode=local):
    - pymupdf (PyMuPDF) → parsing PDF accurato

- Librerie Facoltative:
    - ftfy → “ripara” unicode (apostrofi, spazi invisibili)

Per installare le librerie:

```bash
pip install fastapi uvicorn pymupdf ftfy
```

Per provare subito senza PyMuPDF, puoi usare mode=ocr e non installare pymupdf.

## 🔌 Endpoint

```
GET /health
```

Verifica rapido del servizio.

200 OK → {"status": "ok"}

```
POST /parse
```

Form-data: file (PDF)

Query:

mode=local|ocr (default local)

language=ita|eng|... (per OCR)


## 🧠 Scelte progettuali (in breve)

* Separa responsabilità:

extractors: solo estrazione di testo, non interpreta nulla.

parsers: capisce “cosa c’è scritto” (nome, lingue, esperienze…).

normalizers: adatta al tuo schema e pulisce i dati.

scoring: calcola una metrica semplice per la UI.

* Fallback:

Se PyMuPDF manca → usa OCR.

Se non troviamo una sezione → non esplode: riempie il minimo sindacale.

* Internazionale:

Regex neutrali su lingue, date, indirizzi (senza liste chiuse di professioni).


## 🧾 Licenza

MIT — usa, modifica, condividi.
Se ti è utile, lascia una ⭐ al repo.


## Autore



## JSON di output

Questo è il JSON di esempio in cui devi generare le informazioni: 

```JSON
{ "anagrafica": 
    { 
        "nome": "", 
        "cognome": "", 
        "data_nascita": "", 
        "luogo_nascita": "", 
        "nazionalita": "", 
        "sesso": "", 
        "stato_civile": "" 
    }, 
    "contatti": 
        { 
            "indirizzo": 
                { 
                    "via": "", 
                    "citta": "", 
                    "cap": "", 
                    "provincia": "", 
                    "paese": "" 
                }, 
            "telefono": "", 
            "cellulare": "",
            "email": "", 
            "linkedin": "", 
            "sito_web": "", 
            "github": "" }, 
            "istruzione": 
                [ 
                    { 
                    "titolo_studio": "", 
                    "istituto": "", 
                    "citta": "", 
                    "paese": "", 
                    "data_inizio": "", 
                    "data_fine": "", 
                    "voto": "", 
                    "descrizione": "", 
                    "tesi": "" 
                    }
                ], 
                
            "esperienze_lavorative": 
                [ 
                    { 
                        "posizione": "", 
                        "azienda": "", 
                        "citta": "", 
                        "paese": "", 
                        "data_inizio": "", 
                        "data_fine": "", 
                        "descrizione": "", 
                        "responsabilita": [], 
                        "risultati_ottenuti": [] 
                    } 
                ], 
                
            "competenze_tecniche": 
                { 
                    "linguaggi_programmazione": [], 
                    "framework": [], 
                    "database": [], 
                    "strumenti": [], 
                    "metodologie": [], 
                    "altre_competenze": [] 
                }, 
                
            "competenze_linguistiche": 
                [ 
                    { 
                        "lingua": "", 
                        "livello_scritto": "", 
                        "livello_parlato": "", 
                        "certificazioni": [] 
                    } 
                ],
            
            "competenze_trasversali": [], 
            
            "certificazioni": 
                [ 
                    { 
                        "nome": "", 
                        "ente_certificatore": "", 
                        "data_ottenimento": "", 
                        "data_scadenza": "", 
                        "numero_certificato": "" 
                    } 
                ], 
                
            "progetti": 
                [ 
                    { 
                        "nome": "", 
                        "descrizione": "", 
                        "ruolo": "", 
                        "tecnologie": [], 
                        "link": "" 
                    } 
                ], 
            
            "pubblicazioni": 
                [ 
                    { 
                        "titolo": "", 
                        "autori": [], 
                        "data": "", 
                        "rivista_conferenza": "", 
                        "link": "" 
                    } 
                ], 
                
            
            "interessi": [], 
            "patente": [], 
            "autorizzazione_trattamento_dati": "", 
            "disponibilita": 
                { 
                    "trasferte": "", 
                    "trasferimento": "", 
                    "tipo_contratto_preferito": [] 
                } 
}
```