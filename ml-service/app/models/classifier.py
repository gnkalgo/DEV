"""Signal classification model for BUY / SELL / HOLD."""

import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from app.features.technical import FEATURE_COLUMNS


class SignalClassifier:
    LABELS = ["HOLD", "BUY", "SELL"]

    def __init__(self, model_path: str = "./models/registry/signal_classifier.joblib"):
        self.model_path = Path(model_path)
        self.model: RandomForestClassifier | None = None
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        self.model.fit(X_train, y_train)
        accuracy = self.model.score(X_test, y_test)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        return {"accuracy": accuracy, "model_path": str(self.model_path)}

    def predict(self, features: np.ndarray) -> dict:
        if self.model is None:
            return {"action": "HOLD", "confidence": 0.0, "model_loaded": False}

        proba = self.model.predict_proba(features.reshape(1, -1))[0]
        idx = int(np.argmax(proba))
        return {
            "action": self.LABELS[idx],
            "confidence": round(float(proba[idx]), 4),
            "probabilities": {self.LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)},
            "model_loaded": True,
        }

    @staticmethod
    def label_from_returns(future_return: float, threshold: float = 0.005) -> int:
        if future_return > threshold:
            return 1  # BUY
        if future_return < -threshold:
            return 2  # SELL
        return 0  # HOLD
