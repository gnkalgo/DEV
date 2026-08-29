"""Technical indicator feature engineering for Indian equities."""

import pandas as pd
import ta


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute ML features from OHLCV dataframe. Expects columns: open, high, low, close, volume."""
    df = df.copy()
    df["returns_1d"] = df["close"].pct_change(1)
    df["returns_5d"] = df["close"].pct_change(5)
    df["rsi_14"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["macd"] = ta.trend.MACD(df["close"]).macd()
    df["macd_signal"] = ta.trend.MACD(df["close"]).macd_signal()
    df["bb_upper"] = ta.volatility.BollingerBands(df["close"]).bollinger_hband()
    df["bb_lower"] = ta.volatility.BollingerBands(df["close"]).bollinger_lband()
    df["volume_sma_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_sma_20"]
    df["atr_14"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    return df.dropna()


FEATURE_COLUMNS = [
    "returns_1d",
    "returns_5d",
    "rsi_14",
    "macd",
    "macd_signal",
    "volume_ratio",
    "atr_14",
]
