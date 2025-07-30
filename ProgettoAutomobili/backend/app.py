from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

app = Flask(__name__)
CORS(app)

# Carica dati
df = pd.read_csv('auto_dataset.csv')

# Allena il modello
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
slope = float(test_model.coef_[0])
intercept = float(test_model.intercept_)

# Endpoint: prezzo stimato
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    km = data.get('kilometers', 0)
    price = max(2000, round(slope * km + intercept))
    return jsonify({'price': price})

# Endpoint: metrica modello + coefficiente
@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 4),
        'slope': slope,
        'intercept': intercept
    })

# Endpoint: dati per il grafico
@app.route('/regression_data', methods=['GET'])
def regression_data():
    km_vals = list(range(0, 200001, 2000))
    response = []
    for km in km_vals:
        price = max(2000, round(slope * km + intercept))
        response.append({'kilometers': km, 'predictedPrice': price})
    return jsonify(response)

# Endpoint: scatter plot
@app.route('/scatter_data', methods=['GET'])
def scatter_data():
    sample = df.sample(100).sort_values('Kilometers')
    response = sample[['Kilometers', 'Price']].rename(columns={'Kilometers': 'kilometers', 'Price': 'price'})
    return response.to_dict(orient='records')

if __name__ == '__main__':
    app.run(debug=True, port=8000)


















