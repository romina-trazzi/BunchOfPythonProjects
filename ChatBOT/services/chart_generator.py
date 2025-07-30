import matplotlib.pyplot as plt
import yfinance as yf
import uuid
import os

def generate_chart(symbol):
    df = yf.Ticker(symbol).history(period="6mo")
    if df.empty:
        raise ValueError("Nessun dato disponibile per questo simbolo.")

    filename = f"{uuid.uuid4().hex}.png"
    chart_path = os.path.join("output/charts", filename)

    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["Close"], label=symbol)
    plt.title(f"Andamento di {symbol}")
    plt.xlabel("Data")
    plt.ylabel("Prezzo")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    return chart_path