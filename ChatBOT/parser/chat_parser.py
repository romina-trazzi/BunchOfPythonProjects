import requests
import os
from fuzzywuzzy import fuzz

def interpret_message(message):
    message = message.lower()

    if "cos'è" in message or "cosa vuol dire" in message:
        term = message.replace("cos'è", "").replace("cosa vuol dire", "").strip()
        return {"type": "definition", "term": term}

    if "cambio" in message:
        if "euro" in message and "dollaro" in message:
            return {"type": "currency", "base": "EUR", "target": "USD"}
        elif "dollaro" in message and "yen" in message:
            return {"type": "currency", "base": "USD", "target": "JPY"}

    tickers = {"apple": "AAPL", "fiat": "FCA.MI", "tesla": "TSLA"}
    for name, symbol in tickers.items():
        if fuzz.partial_ratio(name, message) > 80:
            return {"type": "stock", "symbol": symbol}

    return {"type": "unknown"}
