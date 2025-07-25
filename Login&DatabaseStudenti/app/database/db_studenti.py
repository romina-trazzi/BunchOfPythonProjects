import sqlite3
import os

class DatabaseStudenti:
    """
    Classe per la gestione del database degli studenti.
    Fornisce metodi CRUD: Create, Read, Update, Delete.
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.crea_tabella_studenti()

    def connessione(self):
        """
        Crea una nuova connessione SQLite.
        """
        return sqlite3.connect(self.db_path)

    def crea_tabella_studenti(self):
        """
        Crea la tabella 'studenti' se non esiste.
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
        Restituisce un dizionario con i dati dello studente dato l'ID.
        """
        with self.connessione() as conn:
            cursor = conn.execute(
                "SELECT id, nome, cognome, voto FROM studenti WHERE id = ?",
                (studente_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "cognome": row[2],
                    "voto": row[3]
                }
            return None

    def elimina_studente(self, studente_id):
        """
        Elimina uno studente dal database tramite ID.
        Ritorna il numero di righe cancellate (0 se non trovato).
        """
        with self.connessione() as conn:
            cur = conn.execute(
                "DELETE FROM studenti WHERE id = ?",
                (studente_id,)
            )
            conn.commit()
            return cur.rowcount

    def modifica_studente(self, studente_id, nome=None, cognome=None, voto=None):
        """
        Modifica uno o più campi di uno studente dato l'ID.
        Esempio:
            modifica_studente(1, nome="Anna", voto=30)
        """
        campi = {
            "nome": nome,
            "cognome": cognome,
            "voto": voto
        }
        campi = {k: v for k, v in campi.items() if v is not None}
        if not campi:
            raise ValueError("Nessun campo da modificare.")

        set_clause = ", ".join(f"{col} = ?" for col in campi)
        values = list(campi.values()) + [studente_id]

        with self.connessione() as conn:
            cur = conn.execute(
                f"UPDATE studenti SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cur.rowcount