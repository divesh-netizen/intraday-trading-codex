import asyncio
from datetime import datetime

from app.data.candle_builder import CandleBuilder


class MarketDataManager:
    def __init__(self, broker):
        self.broker = broker
        self.candle_builder = CandleBuilder()
        self.subscriptions: dict[str, str] = {}
        self.latest_ticks: dict[str, dict] = {}
        self.connected = False
        self._task = None
        self.disconnect_callback = None

    def add_stock(self, symbol: str, token: str):
        self.subscriptions[symbol] = token

    def remove_stock(self, symbol: str):
        self.subscriptions.pop(symbol, None)

    def on_disconnect(self):
        self.connected = False
        if self.disconnect_callback:
            self.disconnect_callback()

    def handle_tick(self, tick: dict):
        symbol = tick["symbol"]
        ltp = tick["ltp"]
        ts = datetime.fromisoformat(tick["timestamp"])
        self.latest_ticks[symbol] = tick
        self.candle_builder.process_tick(symbol, ltp, ts)

    async def start(self):
        self.connected = True
        while True:
            try:
                payload = [{"symbol": s, "token": t} for s, t in self.subscriptions.items()]
                if payload:
                    await self.broker.subscribe_ticks(payload, self.handle_tick)
                await asyncio.sleep(1)
            except Exception:
                self.on_disconnect()
                await asyncio.sleep(2)

    def run(self):
        if not self._task:
            self._task = asyncio.create_task(self.start())
