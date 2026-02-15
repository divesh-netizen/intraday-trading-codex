from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.db.models import DailyLedger, TradeLog


def should_square_off(now: datetime) -> bool:
    return now.time() >= time(hour=15, minute=15)


def reset_for_new_day(db: Session):
    open_trades = db.query(TradeLog).filter(TradeLog.status == "OPEN").all()
    for trade in open_trades:
        trade.status = "FORCE_EXIT_PENDING"

    today = date.today()
    for ledger in db.query(DailyLedger).filter(DailyLedger.trading_date < today).all():
        ledger.trading_enabled = False
    db.commit()
