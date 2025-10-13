GLOSSARY = {
    "borsa": "La borsa è un mercato regolamentato dove si comprano e vendono strumenti finanziari.",
    "eur": "EUR è la valuta dell'eurozona.",
    "nyse": "Il NYSE è la Borsa di New York, uno dei principali mercati finanziari mondiali."
}

def get_definition(term):
    return GLOSSARY.get(term.lower(), "Definizione non trovata.")
