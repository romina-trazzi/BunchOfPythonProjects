import requests

# Inserisci qui le tue API Key
GROQ_API_KEY = "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"
OPENROUTER_API_KEY = "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"

def call_groq(prompt):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "Sei un assistente esperto di finanza, in grado di rispondere a domande e creare grafici precisi. Dai risposte semplici, precise e amichevoli e molto educate, per garantire una customer experience ottima. Non divagare su altri argomenti"},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=10
        )
        response.raise_for_status()
        return "[Groq] " + response.json()['choices'][0]['message']['content']
    except Exception as e:
        print("❌ Groq fallito:", e)
        return None

def call_openrouter(prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "LLM-Fallback-Tool"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {"role": "system", "content": "Sei un assistente esperto di finanza, in grado di rispondere a domande e creare grafici precisi. Dai risposte semplici, precise e amichevoli e molto educate, per garantire una customer experience ottima. Non divagare su altri argomenti"},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=10
        )
        response.raise_for_status()
        return "[OpenRouter] " + response.json()['choices'][0]['message']['content']
    except Exception as e:
        print("❌ OpenRouter fallito:", e)
        return None

def ask_llm(prompt):
    print("🧠 Provo con Groq...")
    result = call_groq(prompt)
    if result:
        return result

    print("🔄 Groq non disponibile, passo a OpenRouter...")
    result = call_openrouter(prompt)
    if result:
        return result

    return "❌ Nessun provider ha risposto correttamente."

# Esempio di utilizzo
if __name__ == "__main__":
    prompt = input("📝 Inserisci la tua domanda: ")
    risposta = multi_llm_chat(prompt)
    print("\n💬 Risposta:\n", risposta)
    
    