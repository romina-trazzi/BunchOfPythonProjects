import sqlite3
import os

class DatabaseStudenti:
    """
    Classe di accesso al database per la gestione degli studenti.
    Incapsula tutte le operazioni CRUD (Create, Read, Update, Delete).
    """

    def __init__(self, db_path):
        """
        Inizializza l'oggetto e crea la tabella se non esiste.
        """
        self.db_path = db_path
        self.crea_tabella_studenti()

    def connessione(self):
        """
        Crea una nuova connessione SQLite.
        """
        return sqlite3.connect(self.db_path)

    def crea_tabella_studenti(self):
        """
        Crea la tabella 'studenti' se non esiste nel database.
        """
        with self.connessione() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS studenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cognome TEXT NOT NULL,
                    voto REAL NOT NULL
                )
            """)
            conn.commit()

    def inserisci_studente(self, nome, cognome, voto):
        """
        Inserisce un nuovo studente nel database.
        """
        with self.connessione() as conn:
            conn.execute(
                "INSERT INTO studenti (nome, cognome, voto) VALUES (?, ?, ?)",
                (nome, cognome, voto)
            )
            conn.commit()

    def get_studenti(self):
        """
        Restituisce una lista di tutti gli studenti.
        Ogni elemento è una tupla (nome, cognome, voto, id).
        """
        with self.connessione() as conn:
            cursor = conn.execute("SELECT nome, cognome, voto, id FROM studenti")
            return cursor.fetchall()

    def get_studente_by_id(self, studente_id):
        """
        Restituisce un singolo studente cercato per ID.
        """
        with self.connessione() as conn:
            cursor = conn.execute(
                "SELECT nome, cognome, voto FROM studenti WHERE id = ?",
                (studente_id,)
            )
            return cursor.fetchone()

    def modifica_studente(self, studente_id, nome, cognome, voto):
        """
        Aggiorna i dati di uno studente esistente.
        """
        with self.connessione() as conn:
            conn.execute(
                "UPDATE studenti SET nome = ?, cognome = ?, voto = ? WHERE id = ?",
                (nome, cognome, voto, studente_id)
            )
            conn.commit()

    def elimina_studente(self, studente_id):
        """
        Elimina uno studente dal database tramite ID.
        """
        with self.connessione() as conn:
            conn.execute(
                "DELETE FROM studenti WHERE id = ?",
                (studente_id,)
            )
            conn.commit()