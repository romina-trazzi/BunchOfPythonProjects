# 🚗 Stima Prezzo Auto in base ai Chilometri - App Streamlit

Questa applicazione interattiva ti permette di **stimare il prezzo di un’automobile** in base al numero di **chilometri percorsi**, utilizzando un **modello di regressione lineare**.

---

## ⚙️ Funzionalità Principali

- 🔢 **Inserimento interattivo dei km percorsi** per stimare il prezzo.
- 📉 **Grafico dinamico** con linea di regressione che mostra la relazione km/prezzo.
- 🧮 **Visualizzazione dell’equazione** del modello di regressione: Prezzo = -0.08 × Km + 29834.00
- 📈 **Validazione del modello** su dati reali:
- MAE, RMSE, R²
- 📊 **Analisi dei modelli**:
- Prezzo medio per modello simulato
- Perdita media di valore per km (€/km)
- 📁 **Dataset incluso**: `auto_dataset.csv` con 1000 auto simulate
- ✅ **Interfaccia intuitiva**: sviluppata con [Streamlit](https://streamlit.io), semplice da usare anche per utenti non tecnici.

---

## 🧠 Come funziona

- I dati simulati rappresentano 1000 automobili con km casuali (da 0 a 200.000) e prezzi decrescenti in base ai km.
- Un modello di regressione lineare viene allenato su questi dati.
- L'utente può inserire i chilometri e ottenere un prezzo stimato in tempo reale.
- Il grafico integrato mostra visivamente la relazione tra km e valore del veicolo.

---

## 🚀 Come avviare l'app

1. Installa le dipendenze:
   ```bash
   pip install streamlit scikit-learn matplotlib pandas
   ```

Avvia l'app Streamlit:

```bash
python -m streamlit run app.py
```

Verrà aperta automaticamente nel browser.

📁 File inclusi

1. app.py – codice dell'app Streamlit
2. auto_dataset.csv – dataset di esempio generato
3. README.md – descrizione del progetto
4. genera_dataset.py - script per generare autodataset.csv


Nota:per generare nuovamente un set di dati, si può usare il comando:

```bash
genera_dataset.py (opzionale) 
```


🔧 Requisiti

1. Python 3.8+

Librerie:

2. streamlit
3. pandas
4. numpy
5. scikit-learn
6. matplotlib

📬 Contatti
Creato da Romina Trazzi – Progetto didattico per apprendere machine learning e interfacce in Python. Corso BID 2024-2026