from flask import Blueprint, render_template, request, redirect, session, flash, url_for
import os
from app.database.db_studenti import DatabaseStudenti

# Blueprint per tutte le rotte legate agli studenti
studenti_bp = Blueprint("studenti", __name__)

# Percorso assoluto del database nella cartella instance
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
db_path = os.path.join(BASE_DIR, "instance", "studenti.db")

# Inizializza il gestore del database
db_studenti = DatabaseStudenti(db_path)

# Route: Inserisci nuovo studente
@studenti_bp.route("/inserisci", methods=["GET", "POST"])
def inserisci():
    if "username" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        voto = float(request.form["voto"])

        if 0 <= voto <= 10:
            db_studenti.inserisci_studente(nome, cognome, voto)
            flash("Studente inserito con successo.")
            return redirect(url_for("studenti.elenco"))
        else:
            flash("Il voto deve essere compreso tra 0 e 10.")

    return render_template("inserisci.html")

# Route: Elenco degli studenti
@studenti_bp.route("/elenco")
def elenco():
    if "username" not in session:
        return redirect(url_for("login.login"))

    studenti = db_studenti.get_studenti()
    return render_template("elenco.html", studenti=studenti)

# Route: Modifica studente
@studenti_bp.route("/modifica/<int:studente_id>", methods=["GET", "POST"])
def modifica(studente_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    studente = db_studenti.get_studente_by_id(studente_id)

    if not studente:
        flash("Studente non trovato.")
        return redirect(url_for("studenti.elenco"))

    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        voto = float(request.form["voto"])

        db_studenti.modifica_studente(studente_id, nome, cognome, voto)
        flash("Studente modificato.")
        return redirect(url_for("studenti.elenco"))

    return render_template("modifica.html", studente=studente)

# Route: Elimina studente
@studenti_bp.route("/elimina/<int:studente_id>")
def elimina(studente_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    db_studenti.elimina_studente(studente_id)
    flash("Studente eliminato.")
    return redirect(url_for("studenti.elenco"))