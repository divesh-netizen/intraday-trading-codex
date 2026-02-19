import asyncio
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.state import state
from app.api.routes import algos, control, dashboard, stocks
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.engine.risk import RiskContext
from app.engine.strategy import evaluate
from app.services.ledger import snapshot
from app.services.reset_service import should_square_off


app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
templates = Jinja2Templates(directory="app/ui/templates")

app.include_router(stocks.router, prefix="/api")
app.include_router(algos.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(control.router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
async def on_startup():
    Base.metadata.create_all(bind=engine)
    await state.broker.connect()
    state.market_data.disconnect_callback = lambda: setattr(state.risk_engine, "halted_reason", "WS disconnect")
    state.market_data.run()
    asyncio.create_task(trading_loop())


async def trading_loop():
    while True:
        db = SessionLocal()
        try:
            capital = snapshot(db, await state.broker.fetch_balance())
            if should_square_off(datetime.now()):
                state.risk_engine.halted_reason = "Auto square-off window"

            for algo_name, algo in state.algo_manager.algos.items():
                if algo_name in state.algo_manager.paused:
                    continue
                for symbol in algo.watchlist:
                    tick = state.market_data.latest_ticks.get(symbol)
                    if not tick:
                        continue
                    candles = state.market_data.candle_builder.get_recent(symbol)
                    decision = evaluate(algo, symbol, candles, tick["ltp"])
                    if not decision:
                        continue
                    ctx = RiskContext(
                        websocket_connected=state.market_data.connected,
                        global_daily_loss=capital.today_pnl,
                        global_max_daily_loss=state.global_max_daily_loss,
                        global_open_positions=sum(state.algo_manager.open_positions_by_algo.values()),
                        global_max_open_positions=state.global_max_open_positions,
                        open_positions_by_algo=state.algo_manager.open_positions_by_algo,
                        trades_by_algo=state.algo_manager.trades_by_algo,
                        algo_pnl=state.algo_manager.algo_pnl,
                    )
                    ok, reason = state.risk_engine.validate(decision, algo, capital, ctx)
                    if not ok:
                        continue
                    trade = await state.execution_engine.execute_trade(db, decision)
                    state.algo_manager.open_positions_by_algo[algo.name] += 1
                    state.algo_manager.trades_by_algo[algo.name] += 1
                    print("Trade opened", trade.id, reason)
            await asyncio.sleep(1)
        finally:
            db.close()


@app.get("/health")
def health():
    return {"ok": True, "broker": state.broker.name}
