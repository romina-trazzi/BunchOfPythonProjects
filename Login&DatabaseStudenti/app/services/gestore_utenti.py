import json
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Costanti configurabili
MAX_TENTATIVI = 3
TEMPO_BLOCCO_MINUTI = 5

class GestoreUtenti:
    """
    Servizio per la gestione degli utenti con autenticazione,
    blocco temporaneo e persistenza su file JSON.
    """

    def __init__(self, file_utenti):
        self.file_utenti = file_utenti
        self.utenti = self.carica_utenti()

    def carica_utenti(self):
        """
        Carica gli utenti dal file JSON, se non esiste lo crea vuoto.
        """
        if not os.path.exists(self.file_utenti):
            with open(self.file_utenti, 'w') as f:
                json.dump({}, f)
        with open(self.file_utenti, 'r') as f:
            return json.load(f)

    def salva_utenti(self):
        """
        Salva il dizionario aggiornato degli utenti nel file JSON.
        """
        with open(self.file_utenti, 'w') as f:
            json.dump(self.utenti, f, indent=4)

    def utente_esiste(self, username):
        """
        Verifica se un utente esiste nel sistema.
        """
        return username in self.utenti

    def is_bloccato(self, username):
        """
        Controlla se l’utente è temporaneamente bloccato.
        Se il tempo è scaduto, sblocca automaticamente.
        """
        utente = self.utenti[username]
        if not utente.get("bloccato"):
            return False

        sblocco_time = datetime.fromisoformat(utente["sblocco"])
        if datetime.now() >= sblocco_time:
            utente["bloccato"] = False
            utente["tentativi"] = 0
            utente["sblocco"] = None
            self.salva_utenti()
            return False

        return True

    def registra_utente(self, username, password):
        """
        Registra un nuovo utente con password hashata.
        Restituisce False se l'utente già esiste.
        """
        if self.utente_esiste(username):
            return False

        self.utenti[username] = {
            "password": generate_password_hash(password),
            "tentativi": 0,
            "bloccato": False,
            "sblocco": None
        }
        self.salva_utenti()
        return True

    def verifica_login(self, username, password):
        """
        Verifica il login:
        - Se utente non esiste → "utente_non_trovato"
        - Se bloccato → "bloccato"
        - Se password corretta → "successo"
        - Se errata → incrementa tentativi, blocca se necessario → "password_errata"
        """
        if not self.utente_esiste(username):
            return "utente_non_trovato"

        utente = self.utenti[username]

        if self.is_bloccato(username):
            return "bloccato"

        if check_password_hash(utente["password"], password):
            utente["tentativi"] = 0
            self.salva_utenti()
            return "successo"
        else:
            utente["tentativi"] += 1
            if utente["tentativi"] >= MAX_TENTATIVI:
                utente["bloccato"] = True
                sblocco_time = datetime.now() + timedelta(minutes=TEMPO_BLOCCO_MINUTI)
                utente["sblocco"] = sblocco_time.isoformat()
            self.salva_utenti()
            return "password_errata"