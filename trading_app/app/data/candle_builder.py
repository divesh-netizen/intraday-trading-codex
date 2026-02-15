from collections import defaultdict
from datetime import datetime


class CandleBuilder:
    def __init__(self):
        self.current = {}
        self.history = defaultdict(list)

    def process_tick(self, symbol: str, ltp: float, ts: datetime):
        key = (symbol, ts.replace(second=0, microsecond=0))
        if symbol not in self.current or self.current[symbol]["bucket"] != key[1]:
            if symbol in self.current:
                closed = self.current[symbol]
                self.history[symbol].append({k: v for k, v in closed.items() if k != "bucket"})
            self.current[symbol] = {
                "bucket": key[1],
                "ts": key[1],
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": 1,
            }
            return

        candle = self.current[symbol]
        candle["high"] = max(candle["high"], ltp)
        candle["low"] = min(candle["low"], ltp)
        candle["close"] = ltp
        candle["volume"] += 1

    def get_recent(self, symbol: str, limit: int = 50):
        return self.history[symbol][-limit:]
