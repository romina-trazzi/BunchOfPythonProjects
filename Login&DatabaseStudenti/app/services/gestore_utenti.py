# Import di librerie e pacchetti

# Per leggere/scrivere dati JSON (persistenza utenti)
import json

# Per verificare l'esistenza del file utenti all'interno del sistema operativo
import os

# Per gestire il tempo e il blocco temporaneo degli utenti
from datetime import datetime, timedelta

# Funzioni sicure per hashare e verificare password
from werkzeug.security import generate_password_hash, check_password_hash


# Definizione di variabili globali

# Costanti configurabili

# Numero massimo di tentativi di login errati prima del blocco
MAX_TENTATIVI = 3

# Durata del blocco temporaneo in minuti
TEMPO_BLOCCO_MINUTI = 5

# Classe GestoreUtenti
class GestoreUtenti:
    """
    Servizio per la gestione degli utenti con autenticazione,
    blocco temporaneo e persistenza su file JSON.
    """

    # Costruttore
    def __init__(self, file_utenti):
        # Percorso al file JSON che contiene gli utenti registrati (utenti.json)
        self.file_utenti = file_utenti

        # Carica i dati degli utenti dal file JSON
        self.utenti = self.carica_utenti()

    # Metodi

    # Carica gli utenti dal file JSON, se non esiste lo crea vuoto.
    def carica_utenti(self):
    
        if not os.path.exists(self.file_utenti):
            with open(self.file_utenti, 'w') as f:
                # Inizializza con dizionario vuoto
                json.dump({}, f)
        with open(self.file_utenti, 'r') as f:
            # Carica il contenuto in memoria
            return json.load(f)
        
        
    #Salva il dizionario aggiornato degli utenti nel file JSON.
    def salva_utenti(self):
        with open(self.file_utenti, 'w') as f:
            # Salva utenti con formattazione leggibile
            json.dump(self.utenti, f, indent=4)

    # Verifica se un utente esiste nel sistema.
    def utente_esiste(self, username):
        return username in self.utenti

    # Controlla se un utente sia temporaneamente bloccato.
    #  Se il tempo è scaduto, sblocca automaticamente.
    def is_bloccato(self, username):
        
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
        
        # Se l'utente è ancora bloccato, la funzione restituisce True
        return True 

    # Registra un nuovo utente con password hashata.
    # Restituisce False se l'utente già esiste.
    def registra_utente(self, username, password):

        if self.utente_esiste(username):
            return False

        self.utenti[username] = {
            "password": generate_password_hash(password),
            "tentativi": 0,
            "bloccato": False,
            "sblocco": None
        }
        self.salva_utenti()

        # Registrazione completata
        return True


    """
    Verifica il login:
    - Se utente non esiste → "utente_non_trovato"
    - Se bloccato → "bloccato"
    - Se password corretta → "successo"
    - Se errata → incrementa tentativi, blocca se necessario → "password_errata"
    """

    def verifica_login(self, username, password):
        if not self.utente_esiste(username):
            return "utente_non_trovato"

        utente = self.utenti[username]

        if self.is_bloccato(username):
            return "bloccato"

        # Login riuscito → azzera i tentativi
        if check_password_hash(utente["password"], password):
            utente["tentativi"] = 0
            self.salva_utenti()
            return "successo"
        else:
            # Password errata → incrementa tentativi
            utente["tentativi"] += 1
            if utente["tentativi"] >= MAX_TENTATIVI:
                utente["bloccato"] = True
                sblocco_time = datetime.now() + timedelta(minutes=TEMPO_BLOCCO_MINUTI)
                # Salva timestamp sblocco
                utente["sblocco"] = sblocco_time.isoformat()
            self.salva_utenti()
            return "password_errata"