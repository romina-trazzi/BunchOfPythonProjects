# Modulo standard per lavorare con database SQLite
import sqlite3
# Utile per gestire file o percorsi dinamici
import os


# Classe per la gestione del database degli studenti.
# Fornisce metodi CRUD: Create, Read, Update, Delete.    
class DatabaseStudenti:

    # Costruttore
    def __init__(self, db_path):

        # Percorso assoluto o relativo del file SQLite
        self.db_path = db_path

        # Assicura che la tabella esista all'avvio del programma se non esiste
        self.crea_tabella_studenti()

    # Crea una nuova connessione a SQLite
    def connessione(self):
        return sqlite3.connect(self.db_path)

    # Crea la tabella 'studenti' se non esiste
    def crea_tabella_studenti(self):
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

    # Inserisce un nuovo studente nel database
    def inserisci_studente(self, nome, cognome, voto):

        with self.connessione() as conn:
            conn.execute(
                "INSERT INTO studenti (nome, cognome, voto) VALUES (?, ?, ?)",
                (nome, cognome, voto)
            )
            conn.commit()


    # Restituisce una lista di tutti gli studenti.
    # Ogni elemento della lista é una tupla (nome, cognome, voto, id).
    def get_studenti(self):
        with self.connessione() as conn:
            cursor = conn.execute("SELECT nome, cognome, voto, id FROM studenti")
            return cursor.fetchall()

    # Restituisce un dizionario con i dati dello studente dato l'ID
    def get_studente_by_id(self, studente_id):
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


    # Elimina uno studente dal database tramite ID.
    # Restituisce il numero di righe cancellate (0 se non trovato).
    def elimina_studente(self, studente_id):
        with self.connessione() as conn:
            cur = conn.execute(
                "DELETE FROM studenti WHERE id = ?",
                (studente_id,)
            )
            conn.commit()
            return cur.rowcount

    # Modifica uno o più campi di uno studente dato l'ID
    #   Esempio:
    #        modifica_studente(1, nome="Anna", voto=30)
    def modifica_studente(self, studente_id, nome=None, cognome=None, voto=None):
        campi = {
            "nome": nome,
            "cognome": cognome,
            "voto": voto
        }

         # Filtra solo i campi forniti (non None)
        campi = {k: v for k, v in campi.items() if v is not None}
        if not campi:
            raise ValueError("Nessun campo da modificare.")

        # Costruzione dinamica della query
        set_clause = ", ".join(f"{col} = ?" for col in campi)
        values = list(campi.values()) + [studente_id]

        with self.connessione() as conn:
            cur = conn.execute(
                f"UPDATE studenti SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cur.rowcount