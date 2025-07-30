from matplotlib import animation
import yfinance as yf
import matplotlib.pyplot as plt
import os


# Funzione per generare il grafico statico
def generate_stock_chart(ticker: str, period: str = '6mo') -> str | None:
    df = yf.download(ticker, period=period)
    if df.empty:
        return None

    output_dir = os.path.join("static", "charts")
    os.makedirs(output_dir, exist_ok=True)
    chart_path = os.path.join(output_dir, f"{ticker}_{period}_chart.png")

    plt.figure(figsize=(10, 5))
    plt.plot(df['Close'], label='Prezzo di chiusura')
    plt.title(f"{ticker} - Prezzo ultimi {period}")
    plt.xlabel("Data")
    plt.ylabel("Prezzo ($)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    return chart_path


# Funzione per generare il grafico animato
def generate_stock_chart_gif(ticker: str, period: str = '6mo') -> str | None:
    df = yf.download(ticker, period=period)
    if df.empty:
        return None

    prices = df['Close'].reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, len(prices))
    ax.set_ylim(prices['Close'].min(), prices['Close'].max())
    ax.set_title(f"{ticker} - Animazione prezzo")
    ax.set_xlabel("Giorni")
    ax.set_ylabel("Prezzo ($)")
    line, = ax.plot([], [], lw=2)

    def animate(i):
        x = list(range(i))
        y = prices['Close'].iloc[:i]
        line.set_data(x, y)
        return line,

    ani = animation.FuncAnimation(fig, animate, frames=len(prices), interval=30, blit=True)

    output_dir = os.path.join("static", "charts")
    os.makedirs(output_dir, exist_ok=True)
    gif_path = os.path.join(output_dir, f"{ticker}_{period}_chart.gif")
    ani.save(gif_path, writer="pillow")
    plt.close()
    return gif_path