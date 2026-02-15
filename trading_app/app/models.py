from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StrategyTemplate(str, Enum):
    ema_crossover = "ema_crossover"
    vwap_reversion = "vwap_reversion"
    breakout = "breakout"


class StockSubscription(BaseModel):
    symbol: str = Field(min_length=2, max_length=32)
    token: str


class AlgoConfig(BaseModel):
    name: str
    template: StrategyTemplate
    stoploss_pct: float = Field(gt=0, lt=20)
    target_pct: float = Field(gt=0, lt=30)
    risk_per_trade: float = Field(gt=0)
    max_trades_per_day: int = Field(gt=0, le=20)
    max_daily_loss: float = Field(gt=0)
    max_open_trades: int = Field(gt=0, le=10)
    capital_per_trade: float = Field(gt=0)
    watchlist: list[str] = Field(default_factory=list)


class TradeDecision(BaseModel):
    algo_name: str
    symbol: str
    side: str
    ltp: float
    stoploss_price: float
    target_price: float
    quantity: int
    reason: str


class PositionView(BaseModel):
    id: int
    algo_name: str
    symbol: str
    entry_price: float
    stoploss_price: float
    target_price: float
    pnl: float
    status: str
    created_at: datetime


class CapitalSnapshot(BaseModel):
    available_balance: float
    used_margin: float
    free_margin: float
    today_pnl: float
    trading_enabled: bool
    warning: str | None = None
