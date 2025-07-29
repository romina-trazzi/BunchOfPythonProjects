import pandas as pd
import numpy as np


# Dati simulati
np.random.seed(42)
kilometers = np.random.randint(0, 200000, size=1000)
prices = [30000 - km * 0.08 + np.random.normal(0, 1000) for km in kilometers]
prices = np.maximum(prices, 1000)

df = pd.DataFrame({
    'Kilometers': kilometers,
    'Price': prices
})

df.to_csv('auto_dataset.csv', index=False)