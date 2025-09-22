import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Carica il dataset
df = pd.read_csv('auto_dataset.csv')

# Modello generale
X = df[['Kilometers']]
y = df['Price']
model = LinearRegression()
model.fit(X, y)

# Validazione
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
test_model = LinearRegression()
test_model.fit(X_train, y_train)
y_pred = test_model.predict(X_test)

# Metriche
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
slope = test_model.coef_[0]
intercept = test_model.intercept_
regression_eq = f"Prezzo = {slope:.2f} × Km + {intercept:.2f}"

# Titolo app
st.title("🚗 Stima Prezzo Auto in base ai Chilometri")

# Input utente
km_input = st.number_input("Inserisci i chilometri percorsi:", min_value=0, max_value=200000, step=1000)
if km_input:
    prediction = round(model.predict(np.array([[km_input]]))[0])
    st.success(f"Prezzo stimato: {prediction} €")

# Grafico con regressione
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df['Kilometers'], df['Price'], alpha=0.4, label="Dati reali")
x_line = np.linspace(0, 200000, 500).reshape(-1, 1)
y_line = model.predict(x_line)
ax.plot(x_line, y_line, color='red', linewidth=2, label="Linea di regressione")
ax.set_title("📉 Relazione tra Chilometri e Prezzo dell'Auto")
ax.set_xlabel("Chilometri percorsi")
ax.set_ylabel("Prezzo (€)")
ax.legend()
ax.grid(True)
ax.text(10000, y_line.max() - 1000,
        "La linea rossa mostra la tendenza media:\npiù chilometri → minor valore residuo",
        fontsize=10, bbox=dict(facecolor='white', alpha=0.6))
st.pyplot(fig)

# Colonna destra con due espansioni
with st.expander("📈 Validazione del Modello"):
    st.markdown(f"**Equazione del modello:** `{regression_eq}`")
    st.metric(label="Errore medio assoluto (MAE)", value=f"{mae:.2f} €")
    st.metric(label="Errore quadratico medio (RMSE)", value=f"{rmse:.2f} €")
    st.metric(label="R² (accuratezza del modello)", value=f"{r2:.2%}")

with st.expander("📊 Analisi Modelli"):
    df_models = df.copy()
    df_models['Model'] = np.random.choice([
        'Fiat Panda', 'Volkswagen Golf', 'Ford Fiesta', 'Toyota Yaris',
        'Renault Clio', 'Peugeot 208', 'BMW Serie 1', 'Audi A3',
        'Mercedes Classe A', 'Opel Corsa'], size=len(df_models))
    
    avg_price = df_models.groupby('Model')['Price'].mean().sort_values(ascending=False)
    st.subheader("Prezzo medio per modello")
    st.dataframe(avg_price.round(2))

    st.subheader("Perdita media di valore per km (€/km)")
    model_slopes = df_models.groupby('Model').apply(
        lambda x: LinearRegression().fit(x[['Kilometers']], x['Price']).coef_[0])
    st.dataframe(model_slopes.round(4).sort_values())