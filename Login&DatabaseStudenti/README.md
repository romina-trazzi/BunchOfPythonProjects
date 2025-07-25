## 🔐 Sistema di Login + Gestione Studenti

Applicazione web in Python (Flask) con autenticazione sicura, logging e gestione CRUD degli studenti con database SQLite.

---

## 🚀 Funzionalità principali

- Login sicuro con tentativi limitati (max 3)
- Blocco temporaneo di 5 minuti dopo troppi tentativi falliti
- Password hashate (sicurezza tramite `werkzeug.security`)
- Persistenza degli utenti su file JSON
- Log degli accessi su file di testo
- Gestione studenti con operazioni CRUD
- Validazione dei voti (tra 0 e 10)
- Interfaccia web in Flask con template HTML

---

## 📁 Struttura del progetto

LoginApp/
├── run.py # Punto di avvio dell'app Flask
├── instance/ # File persistenti (non tracciati da Git)
│ ├── studenti.db # Database SQLite degli studenti
│ ├── utenti.json # Utenti registrati
│ └── access_log.txt # Log degli accessi
├── app/
│ ├── init.py # Factory Flask + registrazione blueprint
│ ├── models/ # db_studenti.py, gestore_utenti.py, logger_accessi.py
│ ├── routes/ # login_routes.py, studenti_routes.py
│ ├── templates/ # Template HTML Jinja2
│ └── static/ # (Opzionale) CSS/JS personalizzati
└── README.md


---

## ⚙️ Requisiti

- Python 3.10+
- Flask

### 📦 Installazione

```bash
git clone https://github.com/tuo-username/LoginApp.git
cd "Login&DatabaseStudenti" # Come stringa, perché & è un carattere riservato
python -m venv venv
source venv/bin/activate       # Windows: .\venv\Scripts\activate
pip install flask
```

### Avvio dell'app

```bash
python run.py
```

Poi visita http://127.0.0.1:5000 nel browser.

## 📦 Dipendenze principali

| Funzionalità            | Libreria              |
|-------------------------|------------------------|
| Web framework           | `flask`                |
| Sicurezza password      | `werkzeug.security`    |
| Log e data handling     | `datetime`, `os`, `json` |
| Database                | `sqlite3`              |


## 📌 Note

* I dati degli utenti sono salvati in instance/utenti.json
* Gli studenti sono nel database instance/studenti.db
* I log di login/registrazione sono in instance/access_log.txt
* Il database si crea automaticamente al primo avvio

## 🔒 Sicurezza

* Le password sono hashate, non salvate in chiaro
* Nessuna informazione sensibile viene stampata o loggata

## 🧩 Estensioni future

* Ruoli (admin, docente)
* Ricerca e filtro studenti
* Download CSV/PDF degli studenti
* Interfaccia responsiva (Bootstrap, PicoCSS)
* API REST con Flask

### 👩‍💻 Autore

Romina Trazzi
Full Stack Developer · Appassionata di storia, scacchi, letteratura e cucina
Stack: HTML, CSS, JS, React, Java, PHP, C#, SQL, Python

### 🪪 Licenza

MIT – Libero utilizzo e modifica con attribuzione