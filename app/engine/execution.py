import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import SystemEvent, TradeLog
from app.models import TradeDecision
from app.services.alerts import send_telegram_alert


class ExecutionEngine:
    def __init__(self, broker):
        self.broker = broker
        self.order_keys: set[str] = set()

    async def execute_trade(self, db: Session, decision: TradeDecision) -> TradeLog:
        dedupe_key = f"{decision.algo_name}:{decision.symbol}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        if dedupe_key in self.order_keys:
            raise ValueError("Duplicate order prevented")
        self.order_keys.add(dedupe_key)

        payload = {
            "symbol": decision.symbol,
            "side": decision.side,
            "qty": decision.quantity,
            "price": decision.ltp,
            "product": "INTRADAY",
            "order_type": "LIMIT",
        }

        order_response = await self._retry(self.broker.place_limit_order, payload)
        if order_response.get("status") != "success":
            self._log_event(db, "ERROR", "ORDER_FAILED", str(order_response))
            raise RuntimeError("Entry order failed")

        sl_payload = payload | {"trigger_price": decision.stoploss_price, "price": decision.stoploss_price}
        sl_response = await self._retry(self.broker.place_stoploss_order, sl_payload)
        if sl_response.get("status") != "success":
            self._log_event(db, "ERROR", "SL_FAILED", str(sl_response))
            raise RuntimeError("SL placement failed; entry should be exited manually")

        row = TradeLog(
            algo_name=decision.algo_name,
            symbol=decision.symbol,
            side=decision.side,
            quantity=decision.quantity,
            entry_price=decision.ltp,
            stoploss_price=decision.stoploss_price,
            target_price=decision.target_price,
            broker_order_id=order_response.get("order_id"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        await send_telegram_alert(f"ENTRY: {decision.algo_name} {decision.symbol} @ {decision.ltp}")
        return row

    async def _retry(self, fn, payload):
        error = None
        for _ in range(settings.broker_retry_attempts):
            try:
                return await fn(payload)
            except Exception as exc:
                error = exc
                await asyncio.sleep(0.5)
        raise RuntimeError(f"Broker API failed repeatedly: {error}")

    @staticmethod
    def _log_event(db: Session, level: str, event_type: str, message: str):
        db.add(SystemEvent(level=level, event_type=event_type, message=message))
        db.commit()
