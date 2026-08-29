"""SMC intraday signal evaluation on OHLC candles (entry, stop loss, target)."""

from dataclasses import dataclass
from typing import Literal

EntryMode = Literal["order_block", "fvg", "bos"]
SideMode = Literal["BUY", "SELL", "AUTO"]


@dataclass
class SmcSignal:
    should_trade: bool
    side: Literal["BUY", "SELL"] | None = None
    entry: float | None = None
    stop_loss: float | None = None
    target: float | None = None
    reason: str = ""


def _swing_low(candles: list[dict], lookback: int = 5) -> float:
    window = candles[-lookback:]
    return min(c["low"] for c in window)


def _swing_high(candles: list[dict], lookback: int = 5) -> float:
    window = candles[-lookback:]
    return max(c["high"] for c in window)


def _bullish_fvg(candles: list[dict]) -> bool:
    if len(candles) < 3:
        return False
    c1, _, c3 = candles[-3], candles[-2], candles[-1]
    return c3["low"] > c1["high"]


def _bearish_fvg(candles: list[dict]) -> bool:
    if len(candles) < 3:
        return False
    c1, _, c3 = candles[-3], candles[-2], candles[-1]
    return c3["high"] < c1["low"]


def _bullish_order_block(candles: list[dict]) -> bool:
    if len(candles) < 2:
        return False
    prev, cur = candles[-2], candles[-1]
    prev_bear = prev["close"] < prev["open"]
    cur_bull = cur["close"] > cur["open"] and cur["close"] > prev["open"]
    return prev_bear and cur_bull


def _bearish_order_block(candles: list[dict]) -> bool:
    if len(candles) < 2:
        return False
    prev, cur = candles[-2], candles[-1]
    prev_bull = prev["close"] > prev["open"]
    cur_bear = cur["close"] < cur["open"] and cur["close"] < prev["open"]
    return prev_bull and cur_bear


def _bullish_bos(candles: list[dict], lookback: int = 10) -> bool:
    if len(candles) < lookback + 1:
        return False
    prior = candles[-(lookback + 1):-1]
    last = candles[-1]
    return last["close"] > _swing_high(prior, len(prior))


def _bearish_bos(candles: list[dict], lookback: int = 10) -> bool:
    if len(candles) < lookback + 1:
        return False
    prior = candles[-(lookback + 1):-1]
    last = candles[-1]
    return last["close"] < _swing_low(prior, len(prior))


def evaluate_smc_intraday(
    candles: list[dict],
    entry_mode: EntryMode = "fvg",
    side_mode: SideMode = "AUTO",
    buffer_pct: float = 0.1,
    target_rr: float = 2.0,
    swing_lookback: int = 5,
) -> SmcSignal:
    if len(candles) < 10:
        return SmcSignal(False, reason="insufficient_candles")

    last = candles[-1]
    entry = float(last["close"])

    bullish = False
    bearish = False
    if entry_mode == "fvg":
        bullish = _bullish_fvg(candles)
        bearish = _bearish_fvg(candles)
    elif entry_mode == "order_block":
        bullish = _bullish_order_block(candles)
        bearish = _bearish_order_block(candles)
    elif entry_mode == "bos":
        bullish = _bullish_bos(candles)
        bearish = _bearish_bos(candles)

    side: Literal["BUY", "SELL"] | None = None
    if side_mode == "BUY" and bullish:
        side = "BUY"
    elif side_mode == "SELL" and bearish:
        side = "SELL"
    elif side_mode == "AUTO":
        if bullish and not bearish:
            side = "BUY"
        elif bearish and not bullish:
            side = "SELL"
    elif side_mode == "BUY" and not bullish:
        return SmcSignal(False, reason=f"no_{entry_mode}_buy_setup")
    elif side_mode == "SELL" and not bearish:
        return SmcSignal(False, reason=f"no_{entry_mode}_sell_setup")

    if side is None:
        return SmcSignal(False, reason=f"no_{entry_mode}_setup")

    buffer = buffer_pct / 100.0
    if side == "BUY":
        sl_base = _swing_low(candles, swing_lookback)
        stop_loss = round(sl_base * (1 - buffer), 2)
        risk = entry - stop_loss
        if risk <= 0:
            return SmcSignal(False, reason="invalid_risk_buy")
        target = round(entry + risk * target_rr, 2)
    else:
        sl_base = _swing_high(candles, swing_lookback)
        stop_loss = round(sl_base * (1 + buffer), 2)
        risk = stop_loss - entry
        if risk <= 0:
            return SmcSignal(False, reason="invalid_risk_sell")
        target = round(entry - risk * target_rr, 2)

    return SmcSignal(
        True,
        side=side,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        reason=f"{entry_mode}_{side.lower()}",
    )
