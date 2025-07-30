import os
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def generate_stock_chart(ticker: str, period: str = "6mo") -> str | None:
    try:
        df = yf.download(ticker, period=period)
        if df.empty:
            return None

        # Salva il grafico nella cartella static
        chart_dir = os.path.join("static", "charts")
        os.makedirs(chart_dir, exist_ok=True)
        filename = f"{ticker}_{period}.png"
        full_path = os.path.join(chart_dir, filename)

        # Genera il grafico
        plt.figure(figsize=(10, 5))
        plt.plot(df["Close"], label="Prezzo di chiusura")
        plt.title(f"{ticker} - Prezzo ultimi {period}")
        plt.xlabel("Data")
        plt.ylabel("Prezzo ($)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(full_path)
        plt.close()

        return f"charts/{filename}"
    
    except Exception as e:
        return None