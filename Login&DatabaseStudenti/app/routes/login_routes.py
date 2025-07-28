# Importa tutto ciò che serve per gestire login, sessione e logging personalizzato.
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
import os
from app.services.gestore_utenti import GestoreUtenti
from app.services.logger_accessi import LoggerAccessi

# Crea un Blueprint chiamato login, che gestisce tutte le rotte di autenticazione.
login_bp = Blueprint("login", __name__)

# Percorsi assoluti ai file in instance/
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # /app/routes
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))  # risale a /Login&DatabaseStudenti
INSTANCE_PATH = os.path.join(PROJECT_ROOT, "instance")

# Garantisci che la cartella instance esista
os.makedirs(INSTANCE_PATH, exist_ok=True)

utenti_path = os.path.join(INSTANCE_PATH, "utenti.json")
log_path = os.path.join(INSTANCE_PATH, "access_log.txt")

# Inizializza i servizi principali
utenti = GestoreUtenti(utenti_path)
logger = LoggerAccessi(log_path)

# Redirect da "/" a "/login" o "/studenti/inserisci"
@login_bp.route("/")
def home():
    if "username" in session:
        # Se loggato, va alla pagina studenti
        return redirect(url_for("studenti.inserisci"))
    # Altrimenti, va alla login
    return redirect(url_for("login.login"))


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        esito = utenti.verifica_login(username, password)

        # Loggin dell'evento
        ip = request.remote_addr
        if esito == "successo":
            evento = "login riuscito"
        elif esito == "utente_non_trovato":
            evento = "login fallito: utente non trovato"
        elif esito == "bloccato":
            evento = "login fallito: account bloccato"
        elif esito == "password_errata":
            evento = "login fallito: password errata"
        else:
            evento = f"login fallito: {esito}"

        # IP utente per log
        logger.log(username, evento, ip)

        # Gestione azioni post login
        if esito == "successo":

            # salva l'utente nella sessione
            session["username"] = username
             # reindirizza a pagina studenti
            return redirect(url_for("studenti.inserisci"))
        
        elif esito == "utente_non_trovato":
            flash("Utente non trovato.")
        elif esito == "bloccato":
            flash("Account temporaneamente bloccato.")
        elif esito == "password_errata":
            flash("Password errata.")

    # Template html visualizzato        
    return render_template("login.html")

# Registrazione utente
@login_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        # Ottieni i dati dal form
        username = request.form["username"]
        password = request.form["password"]
        conferma = request.form["confirm_password"]

        # Controllo password
        if password != conferma:
            flash("Le password non corrispondono.")
            return render_template("register.html")

        # Prendi l'IP utente
        ip = request.remote_addr  

        if utenti.registra_utente(username, password):
            # Scrivi nel file di log l'IP
            logger.log(username, "registrazione", ip)  
            flash("Registrazione completata. Ora puoi accedere.")

            # Reindirizza a login
            return redirect(url_for("login.login"))
        else:
            # Scrivi nel file di log l'IP anche se la registrazione fallisce
            logger.log(username, "registrazione fallita (utente esistente)", ip)  
            flash("Utente già esistente.")

    # Template html visualizzato
    return render_template("register.html")

# Logout
@login_bp.route("/logout")
def logout():
    username = session.get("username", "sconosciuto")
    ip = request.remote_addr
    # Scrivi nel file di log l'IP l'azione di logut
    logger.log(username, "logout", ip)
    
    # Elimina l'utente dalla sessione
    session.pop("username", None)
    flash("Sei uscito correttamente.")

    # Template html visualizzato
    return redirect(url_for("login.login"))