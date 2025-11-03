import csv
import os
import math
from datetime import date, datetime, timedelta


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, 1)


def load_transactions(csv_path: str) -> list:
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                dt = parse_date(row["data"]) if "data" in row else parse_date(row["Data"])  # robustness
                descr = row.get("descrizione", row.get("Descrizione", ""))
                cat = row.get("categoria", row.get("Categoria", ""))
                imp = float(row.get("importo", row.get("Importo", "0")))
                tipo = row.get("tipo", row.get("Tipo", "")).lower()
                rows.append({
                    "data": dt,
                    "descrizione": descr,
                    "categoria": cat,
                    "importo": imp,
                    "tipo": tipo,
                })
            except Exception:
                # salta righe malformate
                continue
    return rows


def aggregate_monthly_expenses(rows: list) -> tuple[list, list]:
    monthly = {}
    for r in rows:
        dt = r["data"]
        imp = r["importo"]
        tipo = r["tipo"]
        if imp < 0 or tipo == "debito":
            k = month_start(dt)
            monthly[k] = monthly.get(k, 0.0) + (-imp if imp < 0 else 0.0)
    months_sorted = sorted(monthly.keys())
    y = [monthly[m] for m in months_sorted]
    return months_sorted, y


def percentile(sorted_vals: list, p: float) -> float:
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if p <= 0:
        return sorted_vals[0]
    if p >= 1:
        return sorted_vals[-1]
    pos = (n - 1) * p
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    frac = pos - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def winsorize(vals: list, p_low: float = 0.10, p_high: float = 0.90) -> list:
    if not vals:
        return []
    s = sorted(vals)
    lo = percentile(s, p_low)
    hi = percentile(s, p_high)
    return [min(max(v, lo), hi) for v in vals]


def build_features(months: list, y: list) -> tuple[list, list]:
    # usa: trend temporale, stagionalità (sin/cos) e lag1
    X = []
    y_out = []
    for i in range(1, len(months)):
        m = months[i].month
        phi = 2.0 * math.pi * (m / 12.0)
        sin1 = math.sin(phi)
        cos1 = math.cos(phi)
        trend = float(i)
        lag1 = y[i - 1]
        X.append([1.0, trend, sin1, cos1, lag1])
        y_out.append(y[i])
    return X, y_out


def mat_vec_mult(A: list, x: list) -> list:
    return [sum(aij * xj for aij, xj in zip(ai, x)) for ai in A]


def transpose(A: list) -> list:
    return [list(row) for row in zip(*A)]


def normal_equation(X: list, y: list) -> tuple[list, list]:
    XT = transpose(X)
    # XTX
    XTX = [[sum(a * b for a, b in zip(row_i, col_j)) for col_j in XT] for row_i in XT]
    # XTy
    XTy = [sum(xi * yi for xi, yi in zip(col, y)) for col in XT]
    return XTX, XTy


def solve_linear_system(A: list, b: list) -> list:
    n = len(b)
    M = [row[:] + [bb] for row, bb in zip(A, b)]
    for j in range(n):
        # pivoting
        piv = max(range(j, n), key=lambda i: abs(M[i][j]))
        if abs(M[piv][j]) < 1e-12:
            raise ValueError("Sistema singolare")
        M[j], M[piv] = M[piv], M[j]
        # normalizza riga piv
        pivval = M[j][j]
        for k in range(j, n + 1):
            M[j][k] /= pivval
        # elimina
        for i in range(n):
            if i == j:
                continue
            fac = M[i][j]
            for k in range(j, n + 1):
                M[i][k] -= fac * M[j][k]
    return [M[i][n] for i in range(n)]


def fit_linear_regression(X: list, y: list) -> list:
    A, b = normal_equation(X, y)
    beta = solve_linear_system(A, b)
    return beta


def predict_row(beta: list, x: list) -> float:
    return sum(bi * xi for bi, xi in zip(beta, x))


def r2_score(y_true: list, y_pred: list) -> float:
    if not y_true:
        return 0.0
    y_mean = sum(y_true) / len(y_true)
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    ss_tot = sum((yt - y_mean) ** 2 for yt in y_true)
    if ss_tot == 0:
        return 1.0
    return 1.0 - ss_res / ss_tot


def write_prediction(out_dir: str, next_month: date, y_pred: float, r2: float, n_obs: int) -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "previsione_spese.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anno_mese", "spesa_prevista", "r2", "osservazioni_usate"])
        w.writerow([f"{next_month.year}-{next_month.month:02d}", f"{max(y_pred, 0.0):.2f}", f"{r2:.4f}", n_obs])
    return out_path


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    in_path = os.path.join(base_dir, "data", "csv", "estratto_conto.csv")
    if not os.path.exists(in_path):
        print("CSV non trovato. Esegui prima genera_estratto_conto.py")
        return

    rows = load_transactions(in_path)
    months, y = aggregate_monthly_expenses(rows)
    if len(months) < 3:
        print("Dati insufficienti per la regressione.")
        return

    y_w = winsorize(y, 0.10, 0.90)
    X, y_train = build_features(months, y_w)
    beta = fit_linear_regression(X, y_train)
    y_hat = [predict_row(beta, X[i]) for i in range(len(X))]
    r2 = r2_score(y_train, y_hat)

    last_month = months[-1]
    next_month = add_months(last_month, 1)
    phi = 2.0 * math.pi * (next_month.month / 12.0)
    x_next = [
        1.0,
        float(len(months)),
        math.sin(phi),
        math.cos(phi),
        y_w[-1],
    ]
    y_next = predict_row(beta, x_next)

    out_dir = os.path.join(base_dir, "data", "csv")
    out_path = write_prediction(out_dir, next_month, y_next, r2, len(y_train))
    print(f"Previsione mese {next_month.strftime('%Y-%m')}: {max(y_next, 0.0):.2f} €")
    print(f"R^2 training: {r2:.4f} su {len(y_train)} osservazioni")
    print(f"File salvato: {out_path}")


if __name__ == "__main__":
    main()