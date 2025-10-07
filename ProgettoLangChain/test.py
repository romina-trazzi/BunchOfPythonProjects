import requests
import json
from io import BytesIO

def test_skin_disease_api_with_url():
    """Test dell'API con URL dell'immagine."""
    url = "http://localhost:5000/detect-skin-disease-from-url/"
    
    # URL dell'immagine da testare
    image_url = "https://images.squarespace-cdn.com/content/v1/55b167e3e4b02d875c748259/5bef2c68-8915-4f58-a5bd-05af55f57c90/Facebook+Posts+%283%29.png?format=2500w"
    
    # Prepara i dati del form
    data = {
        "image_url": image_url
    }
    
    print(f"\nTest dell'API locale con URL dell'immagine: {image_url}")
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"Status Code: {response.status_code}")
            print(f"Risultato: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Analisi dei risultati
            if "results" in result:
                print("\nAnalisi dei risultati:")
                for disease, probability in result["results"].items():
                    print(f"- {disease}: {probability*100:.2f}%")
            
            return result
        else:
            print(f"Errore: Status code {response.status_code}")
            print(f"Risposta: {response.text}")
            return {"error": response.text}
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione: {str(e)}")
        return {"error": str(e)}

def test_skin_disease_api_with_file():
    """Test dell'API caricando direttamente il file."""
    url = "http://localhost:5000/detect-skin-disease/"
    
    # URL dell'immagine da scaricare e poi caricare come file
    image_url = "https://images.squarespace-cdn.com/content/v1/55b167e3e4b02d875c748259/5bef2c68-8915-4f58-a5bd-05af55f57c90/Facebook+Posts+%283%29.png?format=2500w"
    
    print(f"\nTest dell'API locale caricando l'immagine come file")
    print(f"Scaricamento dell'immagine da: {image_url}")
    
    try:
        # Scarica l'immagine
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image_data = BytesIO(image_response.content)
        
        # Carica l'immagine all'API
        files = {
            "file": ("image.jpg", image_data, "image/jpeg")
        }
        
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status Code: {response.status_code}")
            print(f"Risultato: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Analisi dei risultati
            if "results" in result:
                print("\nAnalisi dei risultati:")
                for disease, probability in result["results"].items():
                    print(f"- {disease}: {probability*100:.2f}%")
            
            return result
        else:
            print(f"Errore: Status code {response.status_code}")
            print(f"Risposta: {response.text}")
            return {"error": response.text}
    except requests.exceptions.RequestException as e:
        print(f"Errore: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("=== Test del Servizio di Rilevamento Malattie della Pelle ===")
    print("Assicurati che il server sia in esecuzione su http://localhost:5000")
    
    # Test con URL dell'immagine
    test_skin_disease_api_with_url()
    
    # Test caricando il file
    test_skin_disease_api_with_file()