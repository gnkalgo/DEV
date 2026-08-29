"""Batch signal generation pipeline."""

import numpy as np
import pandas as pd

from app.features.technical import compute_features, FEATURE_COLUMNS
from app.models.classifier import SignalClassifier


def generate_signals(ohlcv_data: dict[str, pd.DataFrame], classifier: SignalClassifier) -> list[dict]:
    signals = []
    for symbol, df in ohlcv_data.items():
        featured = compute_features(df)
        if featured.empty:
            continue
        latest = featured.iloc[-1]
        features = latest[FEATURE_COLUMNS].values.astype(float)
        prediction = classifier.predict(features)
        signals.append({
            "symbol": symbol,
            "action": prediction["action"],
            "confidence": prediction["confidence"],
            "price": float(latest["close"]),
            "rsi_14": float(latest["rsi_14"]),
            "features": {col: float(latest[col]) for col in FEATURE_COLUMNS},
        })
    return signals


def create_training_data(ohlcv_data: dict[str, pd.DataFrame], horizon: int = 5) -> tuple[np.ndarray, np.ndarray]:
    X_rows, y_rows = [], []
    classifier = SignalClassifier()

    for df in ohlcv_data.values():
        featured = compute_features(df)
        if len(featured) < horizon + 1:
            continue
        featured["future_return"] = featured["close"].shift(-horizon) / featured["close"] - 1
        featured = featured.dropna()
        for _, row in featured.iterrows():
            X_rows.append(row[FEATURE_COLUMNS].values.astype(float))
            y_rows.append(classifier.label_from_returns(row["future_return"]))

    return np.array(X_rows), np.array(y_rows)
