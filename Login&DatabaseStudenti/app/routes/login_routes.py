from flask import Blueprint, render_template, request, redirect, session, flash, url_for
import os
from app.services.gestore_utenti import GestoreUtenti
from app.services.logger_accessi import LoggerAccessi

# Blueprint per tutte le rotte legate all'autenticazione
login_bp = Blueprint("login", __name__)

# Percorsi ai file nella cartella instance/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
utenti_path = os.path.join(BASE_DIR, "instance", "utenti.json")
log_path = os.path.join(BASE_DIR, "instance", "access_log.txt")

# Inizializzazione gestori utenti e log
utenti = GestoreUtenti(utenti_path)
logger = LoggerAccessi(log_path)

# Rotta per la homepage: reindirizza all'inserimento se loggati
@login_bp.route("/")
def home():
    if "username" in session:
        return redirect(url_for("studenti.inserisci"))
    return redirect(url_for("login.login"))

# Login utente
@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        esito = utenti.verifica_login(username, password)
        logger.log(username, esito)

        if esito == "successo":
            session["username"] = username
            return redirect(url_for("studenti.inserisci"))
        elif esito == "utente_non_trovato":
            flash("Utente non trovato.")
        elif esito == "bloccato":
            flash("Account temporaneamente bloccato.")
        elif esito == "password_errata":
            flash("Password errata.")
    return render_template("login.html")

# Registrazione utente
@login_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conferma = request.form["confirm_password"]

        if password != conferma:
            flash("Le password non corrispondono.")
            return render_template("register.html")

        if utenti.registra_utente(username, password):
            logger.log(username, "registrazione")
            flash("Registrazione completata. Ora puoi accedere.")
            return redirect(url_for("login.login"))
        else:
            flash("Utente già esistente.")
    return render_template("register.html")

# Logout utente
@login_bp.route("/logout")
def logout():
    session.pop("username", None)
    flash("Sei uscito correttamente.")
    return redirect(url_for("login.login"))