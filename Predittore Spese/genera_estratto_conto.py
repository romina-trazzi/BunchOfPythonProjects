import csv
import os
import random
from datetime import date, timedelta


def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def end_of_month(month_start: date) -> date:
    return add_months(month_start, 1) - timedelta(days=1)


def weekday_shift_to_workday(day: date) -> date:
    # Sposta al lunedì se cade nel weekend
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def clamp_amount(x: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, x))


def seasonal_multiplier(month: int) -> float:
    # Inverni più costosi per luce/gas: Nov–Mar
    if month in (11, 12, 1, 2, 3):
        return 1.35
    # Estate: spese fuori casa leggermente maggiori
    if month in (6, 7, 8):
        return 1.10
    return 1.0


def build_merchants():
    return {
        "supermercato": ["Conad", "Coop", "Esselunga", "Carrefour", "Lidl", "Pam", "Eurospin"],
        "ristorante": [
            "Pizzeria Da Mario",
            "Bar Centrale",
            "Trattoria al Ponte",
            "Ristorante La Pergola",
            "Sushi House",
            "Caffetteria Roma",
        ],
        "trasporti": ["ATM Milano", "TPL Urbano", "Trenitalia", "Italo", "Autostrade", "Car Sharing"],
        "carburante": ["Q8", "ENI", "IP", "Shell", "Tamoil"],
        "intrattenimento": ["Netflix", "Spotify", "Amazon Prime", "Cinema UCI"],
        "utenze_internet": ["TIM Fibra", "Vodafone Fibra", "Fastweb", "WindTre"],
        "utenze_energia": ["Enel Energia", "A2A Energia", "Hera", "Iren"],
        "utenze_acqua": ["Acquedotto Comunale", "MM Servizi Idrico", "Acea"],
        "sanita": ["Farmacia Comunale", "Studio Medico", "Analisi di Laboratorio"],
        "varie": ["Amazon", "Ikea", "Zara", "Decathlon", "MediaWorld", "Euronics", "Cartoleria"],
    }


def make_tx(dt: date, desc: str, cat: str, amount: float):
    typ = "credito" if amount >= 0 else "debito"
    return {
        "data": dt,
        "descrizione": desc,
        "categoria": cat,
        "importo": round(amount, 2),
        "tipo": typ,
    }


def generate_month_transactions(month_start: date, merchants: dict) -> list:
    m = month_start.month
    seasonal = seasonal_multiplier(m)
    txs = []

    # Stipendio (deposito mensile)
    stip_day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(25, 28)))
    stipendio = random.gauss(2550, 120)
    txs.append(make_tx(stip_day, "Stipendio Azienda", "Stipendio", abs(stipendio)))

    # Affitto
    rent_day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 3)))
    affitto = random.gauss(950, 15)
    txs.append(make_tx(rent_day, "Affitto Appartamento", "Affitto", -abs(affitto)))

    # Utenze: Internet
    internet_day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(4, 10)))
    internet_provider = random.choice(merchants["utenze_internet"])
    txs.append(make_tx(internet_day, f"{internet_provider}", "Utenze - Internet", -29.9 + random.gauss(0, 1.2)))

    # Utenze: Energia (stagionale)
    energia_day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(10, 20)))
    energia_provider = random.choice(merchants["utenze_energia"])
    energia_base = 60 * seasonal
    energia = random.gauss(energia_base, 12)
    txs.append(make_tx(energia_day, f"{energia_provider}", "Utenze - Luce/Gas", -abs(energia)))

    # Utenze: Acqua
    acqua_day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(15, 25)))
    acqua_provider = random.choice(merchants["utenze_acqua"])
    acqua = random.gauss(22, 3)
    txs.append(make_tx(acqua_day, f"{acqua_provider}", "Utenze - Acqua", -abs(acqua)))

    # Abbonamenti intrattenimento (mensili fissi)
    abon_day1 = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(2, 6)))
    txs.append(make_tx(abon_day1, "Netflix", "Intrattenimento", -17.99 + random.gauss(0, 0.5)))
    abon_day2 = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(6, 12)))
    txs.append(make_tx(abon_day2, "Spotify", "Intrattenimento", -9.99 + random.gauss(0, 0.4)))

    # Supermercato (4–8 volte)
    for _ in range(random.randint(4, 8)):
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        shop = random.choice(merchants["supermercato"])
        amount = clamp_amount(random.gauss(62 * seasonal, 25), 12, 140)
        txs.append(make_tx(day, f"Supermercato {shop}", "Spesa Supermercato", -abs(amount)))

    # Ristoranti/Bar (3–7 volte)
    for _ in range(random.randint(3, 7)):
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        place = random.choice(merchants["ristorante"])
        amount = clamp_amount(random.gauss(27 * seasonal, 15), 6, 95)
        txs.append(make_tx(day, place, "Ristoranti/Bar", -abs(amount)))

    # Trasporti TPL piccoli addebiti (6–14)
    for _ in range(random.randint(6, 14)):
        day = date(month_start.year, month_start.month, random.randint(1, 28))
        amount = random.choice([1.5, 2.0, 2.2, 2.5, 3.0])
        txs.append(make_tx(day, random.choice(merchants["trasporti"]), "Trasporti", -amount))

    # Carburante (1–3)
    for _ in range(random.randint(1, 3)):
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        brand = random.choice(merchants["carburante"])
        amount = clamp_amount(random.gauss(65, 18), 35, 110)
        txs.append(make_tx(day, f"Carburante {brand}", "Trasporti", -abs(amount)))

    # Sanità (0–2)
    for _ in range(random.randint(0, 2)):
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        provider = random.choice(merchants["sanita"])
        amount = clamp_amount(random.gauss(70, 40), 18, 180)
        txs.append(make_tx(day, provider, "Sanità/Assicurazioni", -abs(amount)))

    # Varie (3–6)
    for _ in range(random.randint(3, 6)):
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        vendor = random.choice(merchants["varie"])
        amount = clamp_amount(random.gauss(35 * seasonal, 25), 5, 160)
        txs.append(make_tx(day, f"Acquisto {vendor}", "Varie", -abs(amount)))

    # Rimborso occasionale (0–1)
    if random.random() < 0.25:
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(10, 28)))
        amount = clamp_amount(random.gauss(80, 40), 25, 250)
        txs.append(make_tx(day, "Rimborso spese", "Rimborsi", abs(amount)))

    # Commissione bancaria (0–1)
    if random.random() < 0.3:
        day = weekday_shift_to_workday(date(month_start.year, month_start.month, random.randint(1, 28)))
        amount = clamp_amount(random.gauss(2.5, 0.8), 1.2, 4.5)
        txs.append(make_tx(day, "Commissione bancaria", "Commissioni", -abs(amount)))

    return txs


def add_anomalies(txs_all: list) -> list:
    # Inserisce 2–3 anomalie globali
    anomalies = []
    count = random.choice([2, 2, 3])
    dates = sorted({t["data"] for t in txs_all})
    if not dates:
        return []

    for _ in range(count):
        d = random.choice(dates)
        if random.random() < 0.7:
            # spesa molto grande
            amount = -abs(random.gauss(1200, 450))
            desc = random.choice([
                "Acquisto straordinario (Elettrodomestico)",
                "Riparazione auto imprevista",
                "Spesa medica urgente",
                "Viaggio improvviso",
            ])
            anomalies.append(make_tx(d, desc, "Anomalia - Spesa Straordinaria", amount))
        else:
            # rimborso molto grande
            amount = abs(random.gauss(800, 300))
            desc = random.choice([
                "Rimborso assicurazione",
                "Rimborso doppio addebito",
                "Rimborso acquisto",
            ])
            anomalies.append(make_tx(d, desc, "Anomalia - Rimborso", amount))
    return anomalies


def sort_txs(txs: list) -> list:
    return sorted(txs, key=lambda x: (x["data"], 0 if x["importo"] >= 0 else 1))


def write_csv(txs: list, out_path: str, starting_balance: float = 3000.0) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bal = starting_balance
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "descrizione", "categoria", "importo", "tipo", "saldo"])
        for t in sort_txs(txs):
            bal += t["importo"]
            writer.writerow([
                t["data"].isoformat(),
                t["descrizione"],
                t["categoria"],
                f"{t['importo']:.2f}",
                t["tipo"],
                f"{bal:.2f}",
            ])
    return out_path


def generate_statement(months: int = 12, start_from: date | None = None, seed: int = 42) -> list:
    random.seed(seed)
    merchants = build_merchants()
    today = date.today()
    if start_from is None:
        start_from = date(today.year, today.month, 1)

    # genera mesi passati (months) a partire da start_from - months
    start_month = add_months(start_from, -months)
    txs_all = []
    for i in range(months):
        m_start = add_months(start_month, i)
        txs_all.extend(generate_month_transactions(m_start, merchants))

    # aggiungi anomalie
    txs_all.extend(add_anomalies(txs_all))

    return sort_txs(txs_all)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "data", "csv")
    out_path = os.path.join(out_dir, "estratto_conto.csv")
    txs = generate_statement(months=12, seed=42)
    path = write_csv(txs, out_path, starting_balance=3000.0)
    print(f"Creato CSV: {path}")
    print(f"Transazioni totali: {len(txs)}")


if __name__ == "__main__":
    main()