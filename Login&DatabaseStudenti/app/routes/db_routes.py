# Importa Blueprint, che serve per raggruppare rotte Flask in moduli separati
from flask import Blueprint

# Importa il modello Studente dal file models.py
from app.models import Studente

# Crea un Blueprint chiamato 'main'.
# __name__ serve per dire a Flask dove si trova questo file (necessario per caricare correttamente risorse relative).
main = Blueprint('main', __name__)

# Rotta principale dell'app
# Quando un utente visita http://localhost:5000/, vedrà il messaggio "App Flask è attiva!".
@main.route('/')
def index():
    return 'App Flask è attiva!'

# Ottiene tutti gli studenti dal database con SQLAlchemy
# Crea una stringa HTML con un elenco di studenti, separati da una riga (<br>)
# Es: "1: Mario (12345)<br>2: Anna (54321)"
@main.route('/studenti')
def mostra_studenti():
    studenti = Studente.query.all()
    return '<br>'.join([f'{s.id}: {s.nome} ({s.matricola})' for s in studenti])