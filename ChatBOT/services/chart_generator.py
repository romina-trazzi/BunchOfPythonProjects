import os
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64


def generate_stock_chart_base64(ticker: str, period: str = '6mo') -> str | None:
    try:
        df = yf.download(ticker, period=period)
        if df.empty:
            return None

        plt.figure(figsize=(10, 5))
        plt.plot(df["Close"], label="Prezzo di chiusura")
        plt.title(f"{ticker.upper()} - Prezzo ultimi {period}")
        plt.xlabel("Data")
        plt.ylabel("Prezzo ($)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()\

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format="png")
        plt.close()

        img_bytes.seek(0)
        base64_img = base64.b64encode(img_bytes.read()).decode("utf-8")
        return base64_img
    except Exception as e:
        print(f"[Errore grafico base64]: {e}")
        return None