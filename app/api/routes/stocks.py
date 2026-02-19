from fastapi import APIRouter, HTTPException

from app.main import state
from app.models import StockSubscription

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("")
def list_stocks():
    return state.market_data.subscriptions


@router.post("")
async def add_stock(payload: StockSubscription):
    if len(state.market_data.subscriptions) >= 20:
        raise HTTPException(status_code=400, detail="Max 20 stocks supported")
    valid = await state.broker.validate_token(payload.symbol, payload.token)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid token")
    state.market_data.add_stock(payload.symbol, payload.token)
    return {"status": "subscribed", "symbol": payload.symbol}


@router.delete("/{symbol}")
def remove_stock(symbol: str):
    state.market_data.remove_stock(symbol)
    return {"status": "removed", "symbol": symbol}
