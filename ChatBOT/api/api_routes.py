import os
import yfinance as yf
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request

api_blueprint = Blueprint("api", __name__)

# Pagina di benvenuto
@api_blueprint.route("/")
def home():
    return render_template("index.html")

# Pagina chatbot
@api_blueprint.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

# Pagina ticker
@api_blueprint.route("/ticker", methods=["GET", "POST"])
def ticker():
    chart_path = None
    ticker_symbol = ""

    if request.method == "POST":
        ticker_symbol = request.form["ticker"].upper()
        df = yf.download(ticker_symbol, period="6mo")

        if not df.empty:
            plt.figure(figsize=(10, 5))
            plt.plot(df["Close"], label="Prezzo di chiusura")
            plt.title(f"{ticker_symbol} - Prezzo ultimi 6 mesi")
            plt.xlabel("Data")
            plt.ylabel("Prezzo ($)")
            plt.grid(True)
            plt.legend()

            chart_dir = os.path.join("static", "charts")
            os.makedirs(chart_dir, exist_ok=True)
            chart_filename = f"{ticker_symbol}_chart.png"
            chart_path = f"charts/{chart_filename}"
            plt.savefig(os.path.join(chart_dir, chart_filename))
            plt.close()

    return render_template("ticker.html", chart_path=chart_path, ticker=ticker_symbol)