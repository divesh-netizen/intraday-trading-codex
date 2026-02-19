from dataclasses import dataclass

from app.core.config import settings
from app.models import AlgoConfig, CapitalSnapshot, TradeDecision


@dataclass
class RiskContext:
    websocket_connected: bool
    global_daily_loss: float
    global_max_daily_loss: float
    global_open_positions: int
    global_max_open_positions: int
    open_positions_by_algo: dict[str, int]
    trades_by_algo: dict[str, int]
    algo_pnl: dict[str, float]


class RiskEngine:
    def __init__(self):
        self.halted_reason: str | None = None

    def validate(self, decision: TradeDecision, algo: AlgoConfig, capital: CapitalSnapshot, ctx: RiskContext) -> tuple[bool, str]:
        if not ctx.websocket_connected:
            return False, "WebSocket disconnected; trading paused"
        if capital.available_balance < settings.min_balance_threshold:
            return False, "Balance below ₹1000 threshold"
        if ctx.global_daily_loss <= -ctx.global_max_daily_loss:
            return False, "Global max daily loss reached"
        if ctx.global_open_positions >= ctx.global_max_open_positions:
            return False, "Global max open positions reached"
        if ctx.open_positions_by_algo.get(algo.name, 0) >= algo.max_open_trades:
            return False, "Algo max concurrent trades reached"
        if ctx.trades_by_algo.get(algo.name, 0) >= algo.max_trades_per_day:
            return False, "Algo max trades/day reached"
        if ctx.algo_pnl.get(algo.name, 0) <= -algo.max_daily_loss:
            return False, "Algo max daily loss reached"
        cost = decision.quantity * decision.ltp
        if cost > algo.capital_per_trade:
            return False, "Capital per trade exceeded"
        if cost > capital.free_margin:
            return False, "Insufficient free margin"
        return True, "OK"
