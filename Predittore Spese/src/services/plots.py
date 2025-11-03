import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def plot_income_expense_balance(months, incomes, expenses, balances, out_path: str):
    ensure_dir(out_path)
    plt.figure(figsize=(10,5))
    x = range(len(months))
    plt.bar(x, incomes, width=0.4, label='Entrate', color='#2f855a', align='center')
    plt.bar([i+0.4 for i in x], expenses, width=0.4, label='Spese', color='#c53030', align='center')
    plt.plot(x, balances, label='Saldo', color='#3182ce', marker='o')
    plt.xticks(x, months, rotation=45, ha='right')
    plt.title('Entrate vs Spese con Saldo mensile')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()