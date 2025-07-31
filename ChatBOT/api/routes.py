import os
import yfinance as yf
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request
from services.chart_generator import generate_stock_chart_base64

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/")
def home():
    return render_template("index.html")

@api_blueprint.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@api_blueprint.route("/ticker", methods=["GET", "POST"])
def ticker():
    chart_path = None
    ticker_symbol = ""
    error_message = None
    period = "6mo"  # Default period

    if request.method == "POST":
        ticker_symbol = request.form.get("ticker", "").upper()
        period = request.form.get("period", "6mo")

        print("▶️ Ricevuto:", ticker_symbol, period)

        try:
            chart_path = generate_stock_chart_base64(ticker_symbol, period)
            if not chart_path:
                error_message = "❌ Ticker non valido o nessun dato disponibile."
        except Exception as e:
            error_message = f"Errore: {str(e)}"
            chart_path = None

    return render_template(
        "ticker.html",
        ticker=ticker_symbol,
        selected_period=period,
        chart_image_base64=chart_path,
        error_message=error_message
    )