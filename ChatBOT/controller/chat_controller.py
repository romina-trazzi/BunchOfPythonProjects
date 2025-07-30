import logging
import yfinance as yf

# === Parser messaggi utente ===
from services.chat_parser import interpret_message

# === Servizi finanziari ===
from services.finance_data import get_price
from services.currency_data import get_exchange
from services.glossary import get_definition

# === Grafici e Report ===
from services.chart_generator import generate_stock_chart, generate_stock_chart_gif
from services.pdf_generator import generate_pdf_report

# === LLM fallback ===
from services.openai_chat import ask_llm

# === Logger ===
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


def handle_ticker_request(ticker_symbol: str, period: str) -> str | None:
    """
    Genera un grafico statico PNG per il ticker specificato e periodo selezionato.
    """
    try:
        return generate_stock_chart(ticker_symbol, period)
    except Exception as e:
        logger.error(f"Errore nella generazione grafico PNG per {ticker_symbol} ({period}): {e}")
        return None


def handle_gif_request(ticker_symbol: str, period: str) -> str | None:
    """
    Genera un grafico animato GIF per il ticker specificato e periodo selezionato.
    """
    try:
        return generate_stock_chart_gif(ticker_symbol, period)
    except Exception as e:
        logger.error(f"Errore nella generazione grafico GIF per {ticker_symbol} ({period}): {e}")
        return None


def handle_user_message(message: str) -> str:
    """
    Interpreta e gestisce il messaggio dell'utente, instradandolo verso
    il servizio finanziario corretto o il fallback LLM.
    """
    try:
        intent = interpret_message(message)
        intent_type = intent.get("type")

        match intent_type:
            case "stock":
                symbol = intent["symbol"]
                price = get_price(symbol)
                return f"📈 Il prezzo corrente di {symbol} è {price} USD."

            case "currency":
                rate = get_exchange(intent["base"], intent["target"])
                return f"💱 Il cambio attuale {intent['base']}/{intent['target']} è {rate}."

            case "definition":
                term = intent["term"]
                definition = get_definition(term)
                if definition == "Definizione non trovata.":
                    return ask_llm(f"Spiegami in modo semplice: {term}")
                return definition

            case "graph":
                symbol = intent["symbol"]
                chart_path = generate_stock_chart(symbol, period="6mo")
                return f"📊 Grafico generato per {symbol}: {chart_path}"

            case "report":
                symbol = intent["symbol"]
                df = yf.Ticker(symbol).history(period="6mo")
                chart_path = generate_stock_chart(symbol, period="6mo")
                pdf_path = generate_pdf_report(symbol, chart_path, df.describe().to_html())
                return f"📄 Report PDF creato per {symbol}. Percorso: {pdf_path}"

            case _:
                logger.info("Intent non riconosciuto, passo a LLM.")
                return ask_llm(message)

    except Exception as e:
        logger.exception(f"Errore nella gestione del messaggio: {e}")
        return "❌ Si è verificato un errore. Riprova più tardi."