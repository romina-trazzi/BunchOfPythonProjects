from datetime import datetime
import os

class LoggerAccessi:
    """
    Servizio semplice per registrare i tentativi di login (esito positivo o negativo)
    su un file di log.
    """

    def __init__(self, file_log):
        """
        Inizializza il logger con il percorso del file di log.
        Crea il file se non esiste.
        """
        self.file_log = file_log
        if not os.path.exists(file_log):
            with open(file_log, "w") as f:
                f.write("== Registro accessi ==\n")

    def log(self, username, esito):
        """
        Scrive una riga di log nel formato:
        [timestamp] - username - esito
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.file_log, "a") as f:
            f.write(f"{timestamp} - {username} - {esito}\n")