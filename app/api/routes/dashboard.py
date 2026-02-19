from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TradeLog
from app.main import state
from app.services.ledger import snapshot

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/capital")
async def capital(db: Session = Depends(get_db)):
    balance = await state.broker.fetch_balance()
    return snapshot(db, balance)


@router.get("/positions")
def positions(db: Session = Depends(get_db)):
    rows = db.query(TradeLog).order_by(TradeLog.created_at.desc()).limit(100).all()
    return rows


@router.get("/ticks")
def ticks():
    return state.market_data.latest_ticks
