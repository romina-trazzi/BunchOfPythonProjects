# src/models/expense_regressor.py
# -------------------------------
# Purpose:
#   Concrete regressor implementation for expense prediction.
#   It selects and builds the sklearn estimator based on config.regressor.model_type
#   and its hyperparameters, while reusing BaseExpenseModel for the rest (fit/predict/save).
#
# Supported model_type:
#   - "random_forest"     -> sklearn.ensemble.RandomForestRegressor
#   - "gradient_boosting" -> sklearn.ensemble.GradientBoostingRegressor
#   - "neural_network"    -> sklearn.neural_network.MLPRegressor
#
# Example:
#   from yaml import safe_load
#   import pandas as pd
#   from src.models.expense_regressor import ExpenseRegressor
#
#   cfg = safe_load(open("config/default.yaml"))
#   df  = pd.read_csv(cfg["data"]["raw_path"])
#   model = ExpenseRegressor(cfg).fit(df)
#   preds = model.predict(df)
#   model.save(cfg["training"]["model_save_path"])

from __future__ import annotations

from typing import Dict

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor

from src.models.base_model import BaseExpenseModel


class ExpenseRegressor(BaseExpenseModel):
    """Concrete regression model with estimator built from config."""

    def __init__(self, config: Dict):
        super().__init__(config)

    def build_estimator(self):
        reg_cfg = self.config.get("regressor", {})
        model_type = reg_cfg.get("model_type", "random_forest").lower()
        hp = reg_cfg.get("hyperparameters", {}) or {}

        if model_type == "random_forest":
            # sensible defaults + override from config
            return RandomForestRegressor(
                n_estimators=hp.get("n_estimators", 200),
                max_depth=hp.get("max_depth"),
                min_samples_split=hp.get("min_samples_split", 2),
                min_samples_leaf=hp.get("min_samples_leaf", 1),
                random_state=hp.get("random_state", 42),
                n_jobs=hp.get("n_jobs", -1),
            )

        if model_type == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=hp.get("n_estimators", 200),
                learning_rate=hp.get("learning_rate", 0.1),
                max_depth=hp.get("max_depth", 3),
                random_state=hp.get("random_state", 42),
            )

        if model_type == "neural_network":
            return MLPRegressor(
                hidden_layer_sizes=hp.get("hidden_layer_sizes", (64, 32)),
                activation=hp.get("activation", "relu"),
                solver=hp.get("solver", "adam"),
                learning_rate_init=hp.get("learning_rate_init", 1e-3),
                max_iter=hp.get("max_iter", 300),
                random_state=hp.get("random_state", 42),
            )

        raise ValueError(
            f"Unsupported regressor.model_type '{model_type}'. "
            f"Use one of: random_forest, gradient_boosting, neural_network."
        )
