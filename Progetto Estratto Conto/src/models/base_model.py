# src/models/base_model.py
# ------------------------
# Purpose:
#   Lightweight base class to standardize training, prediction, and persistence
#   for expense models. It wires together:
#     - config (default.yaml)
#     - feature preprocessor (ExpensePreprocessor)
#     - sklearn estimator (built in subclass)
#
# Responsibilities:
#   - Resolve target column from config
#   - Fit: preprocessor.fit + estimator.fit
#   - Predict: transform + estimator.predict
#   - Metrics: MAE / RMSE / R2
#   - Save/Load model bundle with joblib (preprocessor + estimator)
#
# Usage:
#   from yaml import safe_load
#   import pandas as pd
#   from src.models.expense_regressor import ExpenseRegressor
#
#   cfg = safe_load(open("config/default.yaml"))
#   df  = pd.read_csv(cfg["data"]["raw_path"])
#   model = ExpenseRegressor(cfg).fit(df)
#   yhat  = model.predict(df)
#   model.save(cfg["training"]["model_save_path"])
#
#   loaded = ExpenseRegressor.load(cfg["training"]["model_save_path"], cfg)
#   yhat2  = loaded.predict(df)

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.data.preprocessor import ExpensePreprocessor


class BaseExpenseModel(ABC):
    """Base class that glues config, preprocessor and estimator."""

    def __init__(self, config: Dict):
        self.config: Dict = config or {}
        self.prep: ExpensePreprocessor = ExpensePreprocessor(self.config)
        self.estimator = None  # sklearn estimator, created by subclass

        # Resolve target from config
        self.target_col: str = (
            self.config.get("training", {}).get("target")
            or self.config.get("features", {}).get("target_column", "saldo_disponibile")
        )

    # --------- hooks for subclasses ---------
    @abstractmethod
    def build_estimator(self):
        """Create and return the sklearn estimator using self.config."""
        ...

    # --------- core pipeline ---------
    def _split_xy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """Split dataframe into (X_raw, y) using target_col if present."""
        if self.target_col in df.columns:
            y = df[self.target_col].to_numpy(dtype=float)
            X_raw = df.drop(columns=[self.target_col])
        else:
            y = np.array([], dtype=float)
            X_raw = df
        return X_raw, y

    def fit(self, df: pd.DataFrame):
        """Fit preprocessor and estimator on the provided DataFrame."""
        if self.estimator is None:
            self.estimator = self.build_estimator()

        X_raw, y = self._split_xy(df)
        # Fit preprocessor, then estimator
        self.prep.fit(X_raw)
        X = self.prep.transform(X_raw)

        if y.size == 0:
            raise ValueError(
                f"Target column '{self.target_col}' not found in training data."
            )
        self.estimator.fit(X, y)
        return self

    def predict(self, df: pd.DataFrame, *, return_df: bool = False):
        """Predict on new data; if return_df=True, attach y_pred to a copy of df."""
        if self.estimator is None:
            raise RuntimeError("Estimator not built/fitted. Call .fit() or .load() first.")
        X_raw, y_true = self._split_xy(df)
        X = self.prep.transform(X_raw)
        y_pred = self.estimator.predict(X)

        if return_df:
            out = df.copy()
            out["y_pred"] = y_pred
            if y_true.size:
                out["y_true"] = y_true
            return out
        return y_pred

    # --------- metrics ---------
    @staticmethod
    def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Compute MAE, RMSE, and R2 for regression tasks."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = mean_squared_error(y_true, y_pred, squared=False)
        r2 = r2_score(y_true, y_pred)
        return {"mae": float(mae), "rmse": float(rmse), "r2": float(r2)}

    # --------- persistence ---------
    def save(self, path: str) -> str:
        """Save preprocessor + estimator as a single joblib bundle."""
        bundle = {
            "config": self.config,
            "target_col": self.target_col,
            "preprocessor": self.prep,
            "estimator": self.estimator,
        }
        dump(bundle, path)
        return path

    @classmethod
    def load(cls, path: str, config: Optional[Dict] = None) -> "BaseExpenseModel":
        """Load bundle from disk; if a config is passed, it overrides loaded one."""
        bundle = load(path)
        cfg = config or bundle.get("config") or {}
        model = cls(cfg)
        model.target_col = bundle.get("target_col", model.target_col)
        model.prep = bundle["preprocessor"]
        model.estimator = bundle["estimator"]
        return model
