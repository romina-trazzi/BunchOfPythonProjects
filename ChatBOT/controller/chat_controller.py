import yfinance as yf

# Parsing messaggi utente
from services.chat_parser import interpret_message

# Servizi finanziari
from services.finance_data import get_price
from services.currency_data import get_exchange
from services.glossary import get_definition

# Grafici e PDF
from services.chart_generator import generate_chart
from services.pdf_generator import generate_pdf_report

# Fallback: chiamata a LLM se il messaggio è vago o fuori scope
from services.openai_chat import ask_llm


def handle_user_message(message):
    intent = interpret_message(message)

    if intent["type"] == "stock":
        return f"Il prezzo corrente di {intent['symbol']} è {get_price(intent['symbol'])} USD."

    elif intent["type"] == "currency":
        rate = get_exchange(intent["base"], intent["target"])
        return f"Il cambio attuale {intent['base']}/{intent['target']} è {rate}."

    elif intent["type"] == "definition":
        definition = get_definition(intent["term"])
        if definition == "Definizione non trovata.":
            return ask_llm(f"Spiegami in modo semplice: {intent['term']}")
        return definition

    elif intent["type"] == "graph":
        chart_path = generate_chart(intent["symbol"])
        return f"Grafico generato per {intent['symbol']}. Lo trovi in: {chart_path}"

    elif intent["type"] == "report":
        df = yf.Ticker(intent["symbol"]).history(period="6mo")
        chart_path = generate_chart(intent["symbol"])
        pdf_path = generate_pdf_report(intent["symbol"], chart_path, df.describe().to_html())
        return f"Report PDF creato per {intent['symbol']}. Percorso: {pdf_path}"

    # Fallback: se non riconosciuto, chiedi al modello
    else:
        return ask_llm(message)