import os
import yfinance as yf
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request
from services.chart_generator import generate_stock_chart

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/")
def home():
    return render_template("index.html")

@api_blueprint.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@api_blueprint.route("/ticker", methods=["GET", "POST"])
def ticker():
    ticker_symbol = ""
    chart_path = None
    error_message = None

    if request.method == "POST":
        ticker_symbol = request.form.get("ticker", "").strip().upper()

        if not ticker_symbol.isalpha():
            error_message = "❌ Inserisci solo lettere (es. AAPL, TSLA)"
        else:
            chart_path = generate_stock_chart(ticker_symbol)
            if not chart_path:
                error_message = f"❌ Nessun dato trovato o errore per '{ticker_symbol}'"

    return render_template("ticker.html", ticker=ticker_symbol, chart_path=chart_path, error_message=error_message)