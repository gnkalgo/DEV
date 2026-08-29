from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    symbol: str
    features: dict[str, float] = Field(
        description="Feature dict with keys matching FEATURE_COLUMNS"
    )


class PredictResponse(BaseModel):
    symbol: str
    action: str
    confidence: float
    probabilities: dict[str, float] | None = None
    disclaimer: str = "Not investment advice. For educational purposes only."


class TrainRequest(BaseModel):
    symbols: list[str] = Field(default=["RELIANCE", "TCS", "INFY"])
    horizon_days: int = 5


class TrainResponse(BaseModel):
    accuracy: float
    model_path: str
    samples: int
