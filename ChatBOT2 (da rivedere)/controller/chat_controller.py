from parser.chat_parser import interpret_message
from services.finance_data import get_price
from services.currency_data import get_exchange
from services.glossary import get_definition

def handle_user_message(message):
    intent = interpret_message(message)

    if intent["type"] == "stock":
        return f"Il prezzo corrente di {intent['symbol']} è {get_price(intent['symbol'])} USD."
    elif intent["type"] == "currency":
        rate = get_exchange(intent["base"], intent["target"])
        return f"Il cambio attuale {intent['base']}/{intent['target']} è {rate}."
    elif intent["type"] == "definition":
        return get_definition(intent["term"])
    else:
        return "Mi dispiace, non ho capito la tua domanda."
