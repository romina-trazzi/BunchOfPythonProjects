import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Carica la tua chiave da .env

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/models"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    data = response.json()
    print("✅ Modelli disponibili con questa API key:\n")
    for model in data["data"]:
        model_id = model.get("id", "")
        if ":free" in model_id:
            print(f"🆓 {model_id}")
        else:
            print(f"💰 {model_id}")
else:
    print(f"❌ Errore nella richiesta: {response.status_code}")
    print(response.text)