import asyncio
import random
from datetime import datetime

from app.brokers.base import BrokerBase


class AngelBroker(BrokerBase):
    name = "angel"

    def __init__(self):
        self.connected = False
        self._running_feed = False

    async def connect(self) -> None:
        self.connected = True

    async def fetch_balance(self) -> dict:
        return {
            "available_balance": 100000.0,
            "used_margin": 0.0,
            "free_margin": 100000.0,
        }

    async def validate_token(self, symbol: str, token: str) -> bool:
        return bool(symbol and token)

    async def place_limit_order(self, payload: dict) -> dict:
        return {"status": "success", "order_id": f"ANGEL-LMT-{int(datetime.utcnow().timestamp())}"}

    async def place_stoploss_order(self, payload: dict) -> dict:
        return {"status": "success", "order_id": f"ANGEL-SL-{int(datetime.utcnow().timestamp())}"}

    async def exit_position(self, payload: dict) -> dict:
        return {"status": "success", "order_id": f"ANGEL-EXIT-{int(datetime.utcnow().timestamp())}"}

    async def subscribe_ticks(self, subscriptions: list[dict], on_tick):
        self._running_feed = True
        while self._running_feed:
            await asyncio.sleep(1)
            for item in subscriptions:
                on_tick(
                    {
                        "symbol": item["symbol"],
                        "token": item["token"],
                        "ltp": round(random.uniform(100, 1000), 2),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

    def stop_feed(self):
        self._running_feed = False
