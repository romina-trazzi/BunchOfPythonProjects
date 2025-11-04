# src/models/category_classifier.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib

class CategoryClassifier:
    def __init__(self, model_path="models/latest.joblib"):
        self.model_path = model_path
        self.pipeline = None

    def train(self, df: pd.DataFrame):
        # X = tutto tranne 'category', y = 'category'
        X = df.drop(columns=["category"])
        y = df["category"]

        # Identifica colonne
        categorical = ["merchant", "day_of_week"]
        numeric = ["amount", "is_weekend", "month"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                ("num", "passthrough", numeric),
            ]
        )

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        self.pipeline = Pipeline(steps=[
            ("preprocess", preprocessor),
            ("clf", clf)
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.pipeline.fit(X_train, y_train)
        preds = self.pipeline.predict(X_test)
        print("📊 Report di classificazione:")
        print(classification_report(y_test, preds))

        joblib.dump(self.pipeline, self.model_path)
        print(f"✅ Modello salvato in {self.model_path}")
        return {"train_rows": len(X_train), "test_rows": len(X_test)}

    def predict(self, df: pd.DataFrame):
        if self.pipeline is None:
            self.pipeline = joblib.load(self.model_path)
        preds = self.pipeline.predict(df)
        df["predicted_category"] = preds
        return df