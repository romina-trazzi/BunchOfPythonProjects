# Per ottenere l'ora e la data correnti
from datetime import datetime

# Per fare operazioni su file e directory
import os

class LoggerAccessi:
    def __init__(self, file_log):

        # Percorso del file di log
        self.file_log = file_log

        # Crea la cartella che contiene il file di log se non esiste già
        os.makedirs(os.path.dirname(file_log), exist_ok=True)

        # Se il file di log non esiste, lo crea e scrive un'intestazione
        if not os.path.exists(file_log):
            with open(file_log, "w", encoding="utf-8") as f:
                f.write("== Registro accessi ==\n")

    # Metodo per registrare un evento
    def log(self, username, evento, ip=None):
        try:
            # Se il file di log non esiste, lo crea e scrive un'intestazione
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Se l'indirizzo IP non è fornito, imposta un valore di default
            ip = ip or "IP sconosciuto"

            # Debug in console (opzionale, utile durante lo sviluppo)
            print(f"[DEBUG] Scrittura su file log: {self.file_log}")  
            print(f"[DEBUG] Log salvato: {username} - {evento}")
            
            # Apre il file in modalità append e scrive la riga di log
            with open(self.file_log, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - IP: {ip} - Utente: {username} - Evento: {evento}\n")
        except Exception as e:
            # In caso di errore nella scrittura del log, stampa l'errore
            print(f"[LoggerAccessi] Errore nel log: {e}")