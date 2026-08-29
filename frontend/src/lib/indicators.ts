export type Candle = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
};

export function emaSeries(closes: number[], period: number): (number | null)[] {
  if (!closes.length) return [];
  const k = 2 / (period + 1);
  const out: (number | null)[] = [];
  let prev = closes[0];
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      out.push(null);
      if (i === period - 2) {
        const seed = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
        prev = seed;
      }
      continue;
    }
    if (out.length === period - 1 || (i === period - 1 && out[period - 1] === null)) {
      const seed = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
      prev = seed;
      out[i] = prev;
    } else {
      prev = closes[i] * k + prev * (1 - k);
      out[i] = prev;
    }
  }
  // Simpler full pass
  const result: (number | null)[] = [];
  let ema: number | null = null;
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null);
      continue;
    }
    if (ema === null) {
      ema = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
    } else {
      ema = closes[i] * k + ema * (1 - k);
    }
    result.push(ema);
  }
  return result;
}

export function rsiSeries(closes: number[], period = 14): (number | null)[] {
  const result: (number | null)[] = [];
  if (closes.length < period + 1) return closes.map(() => null);

  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d >= 0) gains += d;
    else losses -= d;
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;

  result.push(...Array(period).fill(null));

  for (let i = period; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    const gain = d > 0 ? d : 0;
    const loss = d < 0 ? -d : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    result.push(100 - 100 / (1 + rs));
  }
  return result;
}

export function atrSeries(candles: Candle[], period = 10): (number | null)[] {
  const trs: number[] = [];
  for (let i = 0; i < candles.length; i++) {
    if (i === 0) {
      trs.push(candles[i].high - candles[i].low);
    } else {
      const h = candles[i].high;
      const l = candles[i].low;
      const pc = candles[i - 1].close;
      trs.push(Math.max(h - l, Math.abs(h - pc), Math.abs(l - pc)));
    }
  }
  const result: (number | null)[] = [];
  for (let i = 0; i < trs.length; i++) {
    if (i < period - 1) {
      result.push(null);
      continue;
    }
    if (i === period - 1) {
      result.push(trs.slice(0, period).reduce((a, b) => a + b, 0) / period);
    } else {
      const prev = result[i - 1]!;
      result.push((prev * (period - 1) + trs[i]) / period);
    }
  }
  return result;
}

export type SupertrendPoint = { time: number; value: number; trend: "up" | "down" };

export function supertrendSeries(
  candles: Candle[],
  period = 10,
  multiplier = 3,
): SupertrendPoint[] {
  const atr = atrSeries(candles, period);
  const result: SupertrendPoint[] = [];
  let finalUpper = 0;
  let finalLower = 0;
  let trend: "up" | "down" = "up";

  for (let i = 0; i < candles.length; i++) {
    const c = candles[i];
    const a = atr[i];
    if (a === null) {
      result.push({ time: c.time, value: c.close, trend: trend });
      continue;
    }
    const hl2 = (c.high + c.low) / 2;
    const basicUpper = hl2 + multiplier * a;
    const basicLower = hl2 - multiplier * a;

    if (i === 0 || atr[i - 1] === null) {
      finalUpper = basicUpper;
      finalLower = basicLower;
    } else {
      finalUpper = basicUpper < finalUpper || candles[i - 1].close > finalUpper ? basicUpper : finalUpper;
      finalLower = basicLower > finalLower || candles[i - 1].close < finalLower ? basicLower : finalLower;
    }

    if (trend === "up") {
      if (c.close < finalLower) trend = "down";
    } else if (c.close > finalUpper) {
      trend = "up";
    }

    const value = trend === "up" ? finalLower : finalUpper;
    result.push({ time: c.time, value, trend });
  }
  return result;
}

export function bucketTime(ts: number, intervalSec: number): number {
  return Math.floor(ts / intervalSec) * intervalSec;
}

export function updateCandleBucket(
  candles: Candle[],
  tickTime: number,
  price: number,
  intervalSec: number,
  volumeDelta = 0,
): Candle[] {
  const bucket = bucketTime(tickTime, intervalSec);
  const last = candles[candles.length - 1];
  if (!last) {
    return [{
      time: bucket,
      open: price,
      high: price,
      low: price,
      close: price,
      volume: volumeDelta || null,
    }];
  }
  if (last.time === bucket) {
    const updated = {
      ...last,
      high: Math.max(last.high, price),
      low: Math.min(last.low, price),
      close: price,
      volume: last.volume != null ? last.volume + volumeDelta : volumeDelta || null,
    };
    return [...candles.slice(0, -1), updated];
  }
  if (bucket > last.time) {
    return [
      ...candles,
      {
        time: bucket,
        open: price,
        high: price,
        low: price,
        close: price,
        volume: volumeDelta || null,
      },
    ];
  }
  return candles;
}
