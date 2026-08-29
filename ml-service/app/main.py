from fastapi import FastAPI, HTTPException

from app.models.classifier import SignalClassifier
from app.pipelines.signal_pipeline import create_training_data, generate_signals
from app.schemas import PredictRequest, PredictResponse, TrainRequest, TrainResponse
from app.features.technical import FEATURE_COLUMNS

app = FastAPI(
    title="GnKAlgo ML Service",
    description="AI/ML signal generation for Indian stock market",
    version="0.1.0",
)

classifier = SignalClassifier()


def _mock_ohlcv(symbol: str) -> dict:
    """Generate synthetic OHLCV for demo until broker data pipeline is connected."""
    import pandas as pd
    import numpy as np

    np.random.seed(hash(symbol) % 2**32)
    n = 120
    close = 1000 + np.cumsum(np.random.randn(n) * 10)
    df = pd.DataFrame({
        "open": close + np.random.randn(n) * 2,
        "high": close + np.abs(np.random.randn(n) * 5),
        "low": close - np.abs(np.random.randn(n) * 5),
        "close": close,
        "volume": np.random.randint(100000, 5000000, n),
    })
    return {symbol: df}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gnkalgo-ml", "model_loaded": classifier.model is not None}


@app.post("/ml/v1/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    try:
        features = [request.features[col] for col in FEATURE_COLUMNS]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing feature: {e}")

    import numpy as np
    result = classifier.predict(np.array(features, dtype=float))
    return PredictResponse(
        symbol=request.symbol,
        action=result["action"],
        confidence=result["confidence"],
        probabilities=result.get("probabilities"),
    )


@app.post("/ml/v1/train", response_model=TrainResponse)
async def train(request: TrainRequest):
    ohlcv = {}
    for symbol in request.symbols:
        ohlcv.update(_mock_ohlcv(symbol))

    X, y = create_training_data(ohlcv, horizon=request.horizon_days)
    if len(X) < 50:
        raise HTTPException(status_code=400, detail="Insufficient training samples")

    metrics = classifier.train(X, y)
    return TrainResponse(accuracy=metrics["accuracy"], model_path=metrics["model_path"], samples=len(X))


@app.get("/ml/v1/signals/batch")
async def batch_signals(symbols: str = "RELIANCE,TCS,INFY"):
    symbol_list = [s.strip() for s in symbols.split(",")]
    ohlcv = {}
    for symbol in symbol_list:
        ohlcv.update(_mock_ohlcv(symbol))

    signals = generate_signals(ohlcv, classifier)
    return {
        "signals": signals,
        "disclaimer": "Not investment advice. For educational purposes only.",
    }
