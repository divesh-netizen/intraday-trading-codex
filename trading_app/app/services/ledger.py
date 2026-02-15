from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import DailyLedger, TradeLog
from app.models import CapitalSnapshot


def get_or_create_ledger(db: Session, opening_balance: float) -> DailyLedger:
    today = date.today()
    ledger = db.query(DailyLedger).filter(DailyLedger.trading_date == today).first()
    if ledger:
        return ledger
    ledger = DailyLedger(
        trading_date=today,
        opening_balance=opening_balance,
        used_margin=0,
        free_margin=opening_balance,
        pnl=0,
        trading_enabled=True,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    return ledger


def snapshot(db: Session, balance: dict) -> CapitalSnapshot:
    ledger = get_or_create_ledger(db, opening_balance=balance["available_balance"])
    total_pnl = db.query(func.coalesce(func.sum(TradeLog.pnl), 0)).scalar() or 0
    ledger.pnl = float(total_pnl)
    ledger.used_margin = balance["used_margin"]
    ledger.free_margin = balance["free_margin"]
    db.commit()
    warning = "Balance below threshold" if balance["available_balance"] < 1000 else None
    return CapitalSnapshot(
        available_balance=balance["available_balance"],
        used_margin=ledger.used_margin,
        free_margin=ledger.free_margin,
        today_pnl=ledger.pnl,
        trading_enabled=ledger.trading_enabled,
        warning=warning,
    )
