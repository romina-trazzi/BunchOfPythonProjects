import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter
} from 'recharts';

const CarPriceEstimator = () => {
  const [kilometers, setKilometers] = useState('');
  const [estimatedPrice, setEstimatedPrice] = useState(null);
  const [regressionData, setRegressionData] = useState([]);
  const [scatterData, setScatterData] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [animatePrice, setAnimatePrice] = useState(false);

  useEffect(() => {
    // Fetch regression line data
    fetch("http://localhost:8000/regression_data")
      .then(res => res.json())
      .then(data => setRegressionData(data));

    // Fetch scatter data
    fetch("http://localhost:8000/scatter_data")
      .then(res => res.json())
      .then(data => setScatterData(data));

    // Fetch model metrics
    fetch("http://localhost:8000/metrics")
      .then(res => res.json())
      .then(data => setMetrics(data));
  }, []);

  const predictPrice = async (km) => {
    const response = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kilometers: km }),
    });
    const data = await response.json();
    return data.price;
  };

  const handleCalculate = async () => {
    if (kilometers) {
      const price = await predictPrice(parseInt(kilometers));
      setEstimatedPrice(price);
      setAnimatePrice(true);
      setTimeout(() => setAnimatePrice(false), 600);
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>🚗 Stima Prezzo Auto</h1>

      <div style={{ marginBottom: "1rem" }}>
        <label>Chilometri percorsi: </label>
        <input
          type="number"
          value={kilometers}
          onChange={(e) => setKilometers(e.target.value)}
          min="0"
          max="200000"
        />
        <button onClick={handleCalculate} disabled={!kilometers}>
          Calcola
        </button>
      </div>

      {estimatedPrice && (
        <h2 style={{ color: "green" }}>💰 Prezzo stimato: {estimatedPrice} €</h2>
      )}

      <div style={{ height: 400 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid />
            <XAxis dataKey="kilometers" name="Km" unit=" km" />
            <YAxis dataKey="price" name="Prezzo" unit=" €" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name="Dati reali" data={scatterData} fill="#8884d8" />
            <Line data={regressionData} type="monotone" dataKey="price" stroke="#ff0000" dot={false} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {metrics && (
        <div style={{ marginTop: "2rem" }}>
          <h3>📊 Metriche del modello</h3>
          <p>Equazione del modello: Prezzo = {metrics.slope?.toFixed(2)} × Km + {metrics.intercept?.toFixed(2)}</p>
          <p>MAE: {metrics.mae} €</p>
          <p>RMSE: {metrics.rmse} €</p>
          <p>R²: {(metrics.r2 * 100).toFixed(2)}%</p>
        </div>
      )}
    </div>
  );
};

export default CarPriceEstimator;