# 🧠 K-Means Visualizer – Flask App

Questa applicazione Python interattiva ti permette di **visualizzare il funzionamento dell’algoritmo di clustering K-Means**, passo dopo passo, su un dataset casuale generato dinamicamente.

## 🔍 Funzionalità

- ✅ Generazione automatica di **10.000 punti randomici 2D**.
- ✅ Applicazione di **K-Means clustering** con numero variabile di cluster (K).
- ✅ Creazione automatica di una **GIF animata** che mostra ogni iterazione dell’algoritmo.
- ✅ Interfaccia web semplice e interattiva sviluppata con **Flask**.
- ✅ Possibilità di modificare il numero di cluster direttamente dalla pagina.

## 📂 Struttura del progetto

ProgettoKMeans/
├── app.py # App Flask principale
├── genera_dati.py # Genera dataset randomico
├── requirements.txt # Librerie Python necessarie
├── static/
│ └── kmeans.gif # GIF generata dinamicamente
└── templates/
└── index.html # Interfaccia web HTML

## 🚀 Come eseguire il progetto

### 1. Clona o scarica il progetto

```bash
git clone https://github.com/romina-trazzi/ProgettoKMeans.git
cd ProgettoKMeans
```

### 2. Installa le dipendenze
Assicurati di avere Python 3.10+ installato, poi esegui:

```bash
pip install -r requirements.txt
```

### 3. Avvia l'applicazione

```bash
python app.py
```

Apri il browser su http://127.0.0.1:5000 per iniziare a usare l’app.

🛠 Tecnologie usate

1. Flask – Web framework
2. scikit-learn – Algoritmi ML
3. matplotlib – Grafici e animazioni
4. Pandas & NumPy – Gestione dati

📌 Note aggiuntive

La GIF viene rigenerata ogni volta che cambi il valore di K.
La cartella static/ deve esistere: viene creata automaticamente se non c’è.
Puoi modificare il numero massimo di iterazioni o punti nel file genera_dati.py.

🧑‍🏫 Autore: Romina Trazzi
Questo progetto è stato sviluppato come esercitazione didattica nel corso Python e Machine Learning del corso BID 2024-2026

📃 Licenza
Distribuito con licenza MIT. Sentiti libero di utilizzarlo, modificarlo e condividerlo.