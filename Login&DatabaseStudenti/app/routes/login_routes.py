from flask import Blueprint, render_template, request, redirect, session, flash, url_for
import os
from app.services.gestore_utenti import GestoreUtenti
from app.services.logger_accessi import LoggerAccessi

login_bp = Blueprint("login", __name__)

# Percorsi assoluti ai file in instance/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
INSTANCE_PATH = os.path.join(BASE_DIR, "instance")

# Garantisci che la cartella instance esista
os.makedirs(INSTANCE_PATH, exist_ok=True)

utenti_path = os.path.join(INSTANCE_PATH, "utenti.json")
log_path = os.path.join(INSTANCE_PATH, "access_log.txt")

utenti = GestoreUtenti(utenti_path)
logger = LoggerAccessi(log_path)

@login_bp.route("/")
def home():
    if "username" in session:
        return redirect(url_for("studenti.inserisci"))
    return redirect(url_for("login.login"))

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

@login_bp.route("/logout")
def logout():
    session.pop("username", None)
    flash("Sei uscito correttamente.")
    return redirect(url_for("login.login"))