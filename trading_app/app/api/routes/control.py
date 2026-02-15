from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TradeLog
from app.main import state

router = APIRouter(prefix="/control", tags=["control"])


@router.post("/manual-exit/{trade_id}")
async def manual_exit(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(TradeLog).filter(TradeLog.id == trade_id).first()
    if not trade:
        return {"status": "not_found"}
    await state.broker.exit_position({"symbol": trade.symbol, "qty": trade.quantity})
    trade.status = "MANUAL_EXIT"
    db.commit()
    return {"status": "exited", "trade_id": trade_id}
