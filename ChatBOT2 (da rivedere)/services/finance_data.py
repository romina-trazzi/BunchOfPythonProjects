import yfinance as yf

def get_price(symbol):
    ticker = yf.Ticker(symbol)
    return ticker.info.get("regularMarketPrice", "N/A")
