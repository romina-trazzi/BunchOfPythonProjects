from flask import Flask, request, jsonify
import requests
from io import BytesIO
import os

app = Flask(__name__)

# Configurazione RapidAPI
RAPIDAPI_KEY = "a4e7f3e3c4msh3d5d8d8b17f2c9fp1b1e5djsn3d9f8dfcd4e9"
RAPIDAPI_HOST = "skin-disease-detector.p.rapidapi.com"
RAPIDAPI_URL = "https://skin-disease-detector.p.rapidapi.com/skin_disease_detector"

@app.route('/detect-skin-disease-from-url/', methods=['POST'])
def detect_skin_disease_from_url():
    """
    Rileva malattie della pelle da un'immagine fornita tramite URL.
    """
    try:
        # Ottieni l'URL dell'immagine dalla richiesta
        image_url = request.form.get('image_url')
        if not image_url:
            return jsonify({"error": "Nessun URL dell'immagine fornito"}), 400
        
        # Scarica l'immagine dall'URL
        print(f"Scaricamento dell'immagine da: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        
        # Invia l'immagine all'API RapidAPI
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        files = {
            "image": ("image.jpg", image_data, "image/jpeg")
        }
        
        print("Invio richiesta a RapidAPI...")
        api_response = requests.post(RAPIDAPI_URL, headers=headers, files=files)
        api_response.raise_for_status()
        
        return api_response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta: {str(e)}")
        return jsonify({"error": f"Errore durante la richiesta: {str(e)}"}), 500

@app.route('/detect-skin-disease/', methods=['POST'])
def detect_skin_disease():
    """
    Rileva malattie della pelle da un'immagine caricata direttamente.
    """
    try:
        # Verifica se è stato caricato un file
        if 'file' not in request.files:
            return jsonify({"error": "Nessun file caricato"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nessun file selezionato"}), 400
        
        # Leggi il contenuto del file
        file_content = file.read()
        file_obj = BytesIO(file_content)
        
        # Invia l'immagine all'API RapidAPI
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        files = {
            "image": (file.filename, file_obj, file.content_type)
        }
        
        print("Invio richiesta a RapidAPI...")
        api_response = requests.post(RAPIDAPI_URL, headers=headers, files=files)
        api_response.raise_for_status()
        
        return api_response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta: {str(e)}")
        return jsonify({"error": f"Errore durante la richiesta: {str(e)}"}), 500

if __name__ == "__main__":
    print("Avvio del server Flask per il rilevamento delle malattie della pelle...")
    print("Server disponibile all'indirizzo: http://localhost:5000")
    print("Endpoint disponibili:")
    print("- POST /detect-skin-disease-from-url/ (form-data con campo 'image_url')")
    print("- POST /detect-skin-disease/ (form-data con campo 'file')")
    app.run(host='0.0.0.0', port=5000, debug=True)