import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "ChatbotFinanziario"
}

def ask_llm(message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    model = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"  # ✅ MODELLO VALIDO

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Sei un assistente esperto di finanza, in grado di rispondere a domande e creare grafici precisi. Dai risposte semplici, precise e amichevoli e molto educate, per garantire una customer experience ottima. Non divagare su altri argomenti"},
            {"role": "user", "content": message}
        ]
    }

    try:
        res = requests.post(url, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Errore dall'API: {e}"