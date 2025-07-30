# Importa l'oggetto db (istanza di SQLAlchemy) dal modulo corrente
from . import db

# Definisce una classe "Studente" che rappresenta una tabella del database
class Studente(db.Model):
    # (opzionale) Specifica il nome della tabella nel database. Senza questa riga, Flask userebbe 'studente' (nome della classe in minuscolo).
    __tablename__ = 'studenti'    

    # Crea una colonna 'id' di tipo intero. È la chiave primaria della tabella, quindi ogni studente avrà un ID univoco.
    id = db.Column(db.Integer, primary_key=True)
    
    # Crea una colonna 'nome' che può contenere una stringa lunga fino a 100 caratteri. Non può essere NULL (obbligatoria).
    nome = db.Column(db.String(100), nullable=False)
    
    # Crea una colonna 'matricola' che può contenere una stringa lunga fino a 20 caratteri.
    # Deve essere un valore univoco (non si possono avere due studenti con la stessa matricola) e non può essere NULL (quindi è obbligatoria).
    matricola = db.Column(db.String(20), unique=True, nullable=False)

# Metodo speciale di Python che definisce come mostrare l'oggetto quando lo stampi o lo visualizzi nel terminale (come il ToString in C#).
def __repr__(self):

    # Restituisce una stringa formattata con il nome e la matricola dello studente, utile per il debugging/logging.
    return f"<Studente: {self.nome} - {self.matricola}>"