from statistics import mean

from app.models import AlgoConfig, TradeDecision


def ema(values: list[float], period: int) -> float:
    if not values:
        return 0
    k = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = value * k + result * (1 - k)
    return result


def evaluate(algo: AlgoConfig, symbol: str, candles: list[dict], ltp: float) -> TradeDecision | None:
    if len(candles) < 5:
        return None

    closes = [c["close"] for c in candles]
    if algo.template.value == "ema_crossover":
        if ema(closes[-9:], 5) > ema(closes[-21:], 10):
            return _build_long(algo, symbol, ltp, "EMA crossover")
    elif algo.template.value == "vwap_reversion":
        vwap = mean(closes[-10:])
        if ltp > vwap:
            return _build_long(algo, symbol, ltp, "VWAP continuation")
    elif algo.template.value == "breakout":
        if ltp >= max(closes[-5:]):
            return _build_long(algo, symbol, ltp, "Breakout")
    return None


def _build_long(algo: AlgoConfig, symbol: str, ltp: float, reason: str) -> TradeDecision:
    sl = round(ltp * (1 - algo.stoploss_pct / 100), 2)
    target = round(ltp * (1 + algo.target_pct / 100), 2)
    risk_per_share = max(ltp - sl, 0.01)
    quantity = max(int(algo.risk_per_trade / risk_per_share), 1)
    return TradeDecision(
        algo_name=algo.name,
        symbol=symbol,
        side="BUY",
        ltp=ltp,
        stoploss_price=sl,
        target_price=target,
        quantity=quantity,
        reason=reason,
    )
