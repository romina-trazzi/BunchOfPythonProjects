import os
import requests

def get_definition(term):
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-small-3.1-24b-instruct:free",  # ✅ usa modello gratuito
        "messages": [
            {
                "role": "system",
                "content": "Fornisci una definizione breve e chiara di concetti finanziari."
            },
            {
                "role": "user",
                "content": f"Definisci: {term}"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        # ✅ Estrai il contenuto dal campo corretto
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Errore dall'API: {str(e)}"