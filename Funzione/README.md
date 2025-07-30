# 📉 Gradient Descent Visuale in Python

Questo progetto mostra **visivamente** come funziona l'algoritmo di **Gradient Descent** su una funzione quadratica semplice:

\[
Y(\phi) = (\phi - 3)^2
\]

L'obiettivo è trovare il **minimo** della funzione, cioè il valore di φ per cui l'errore è zero (φ = 3).

---

## 🗂️ Contenuto

- `phy.py` — Codice Python che:
  - Calcola iterativamente il Gradient Descent
  - Mostra i valori di φ passo dopo passo
  - Visualizza un’**animazione dinamica** su grafico `matplotlib`

---

## 🧪 Requisiti

Installa le librerie necessarie con:

```bash
pip install matplotlib numpy
```

▶️ Come eseguire
Posizionati nella cartella dove si trova phy.py e lancia:

```bash
python phy.py
```

Vedrai:
✅ La funzione 

\[
Y(\phi) = (\phi - 3)^2
\]
 
✅ Un punto rosso che scende lungo la curva
✅ Il valore aggiornato di φ a ogni passo

🧠 Teoria
Funzione: Y(φ) = (φ - 3)^2

Gradiente: dY/dφ = 2(φ - 3)

Aggiornamento a ogni passo:

φ = φ - eta * 2 * (φ - 3)

Convergenza garantita se 0 < eta < 1

⚙️ Personalizzazione
Puoi cambiare nel file phy.py:

phi_0 = 0       # Valore iniziale di φ
eta = 0.1       # Learning rate
steps = 20      # Numero di iterazioni

L'animazione si può salvare in formato .gif

---

🧑‍💻 Autore - Romina Trazzi corso BID 2024-2026
Creato come esercizio didattico per comprendere visivamente il funzionamento dell’ottimizzazione tramite Gradient Descent.