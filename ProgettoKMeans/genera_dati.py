# genera_dati.py
import numpy as np
import pandas as pd

def genera_dati(percorso_csv="dati.csv", n_punti=10000, random_state=42):
    np.random.seed(random_state)
    data = np.random.rand(n_punti, 2)
    df = pd.DataFrame(data, columns=["x", "y"])
    df.to_csv(percorso_csv, index=False)

if __name__ == "__main__":
    genera_dati()
    print("Dati generati con successo.")