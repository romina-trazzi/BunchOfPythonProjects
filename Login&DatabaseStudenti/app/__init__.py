from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app.routes.login_routes import login_bp
from app.routes.studenti_routes import studenti_bp
from app.database.db_studenti import dbstudenti_bp  

# Inizializzazione del database SQLite creato come oggetto SQLAlchemy (migliora l'ORM)
db = SQLAlchemy()

# Funzione per inizializzare l'app
def create_app():

    # Percorso per indicare a Flask dove cercare risorse statiche, template, ecc.
    app = Flask(__name__)

    # Configurazione della chiave segreta
    app.secret_key = "una-chiave-super-segreta"

    # Registrazione dei blueprint (= gruppi di rotte che condividono lo stesso prefisso)
    # Queste rotte sono raggruppate per funzionalità nella cartella routes
    # In questo modo, le rotte definite nei file login_routes.py e studenti_routes.py vengono integrate nell'app.
    app.register_blueprint(login_bp)
    app.register_blueprint(studenti_bp)
    app.register_blueprint(dbstudenti_bp)

    
    # Percorso assoluto dell'intero progetto
    # La variabile __file__ contiene il percorso del file attuale, cioè __init__.py
    # La funzione dirname restituisce il percorso della directory padre, quindi app
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Percorso assoluto del database
    db_path = os.path.join(base_dir, 'instance', 'studenti.db')
    
    # Configurazione della connessione di Flask al database
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    # Collegamento del database all'applicazione + inizializzazione di entrambi
    db.init_app(app)
    
    return app







  