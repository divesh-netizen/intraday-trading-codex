# Intraday Equity Trading App (FastAPI)

A modular, local-first intraday equity trading system with strict risk controls.

## 1) Folder Structure

```text
trading_app/
├── app/
│   ├── api/routes/                # REST endpoints (stocks, algos, dashboard, control)
│   ├── brokers/                   # Broker abstraction + Angel adapter
│   ├── core/                      # App settings
│   ├── data/                      # Tick store + 1-min candle builder
│   ├── db/                        # SQLAlchemy database/session/models
│   ├── engine/                    # Strategy, risk, execution, algo manager
│   ├── services/                  # Alerts, ledger, reset/square-off logic
│   ├── ui/static/                 # Minimal JS
│   ├── ui/templates/              # Minimal HTML
│   └── main.py                    # FastAPI app + orchestration loop
├── requirements.txt
└── README.md
```

## 2) Database Schema (SQLite)

### `trade_logs`
- `id` (PK)
- `algo_name`, `symbol`, `side`, `quantity`
- `entry_price`, `exit_price`, `stoploss_price`, `target_price`
- `status` (OPEN/CLOSED/MANUAL_EXIT/FORCE_EXIT_PENDING)
- `broker_order_id`, `pnl`
- `created_at`, `updated_at`

### `daily_ledgers`
- `id` (PK)
- `trading_date` (unique)
- `opening_balance`, `used_margin`, `free_margin`, `pnl`
- `trading_enabled`

### `system_events`
- `id` (PK)
- `level`, `event_type`, `message`, `created_at`

## 3) API Endpoints

- `GET /health`
- `GET /` (dashboard)

### Stocks
- `GET /api/stocks`
- `POST /api/stocks` add stock `{symbol, token}` (max 20, validates token)
- `DELETE /api/stocks/{symbol}`

### Algos
- `GET /api/algos`
- `POST /api/algos` create/update algo config
- `POST /api/algos/{name}/pause`
- `POST /api/algos/{name}/resume`

### Dashboard / Controls
- `GET /api/dashboard/capital`
- `GET /api/dashboard/positions`
- `GET /api/dashboard/ticks`
- `POST /api/control/manual-exit/{trade_id}`

## 4) Core Execution Flow

1. Start app; initialize DB, broker, data feed task, trading loop.
2. User adds stocks and algos via API/UI.
3. Market data manager receives live ticks and builds 1-min candles.
4. Trading loop evaluates each active algo over watchlist symbols.
5. Strategy emits `TradeDecision`.
6. Risk engine validates global + per-algo constraints.
7. Execution engine places LIMIT entry; immediately places SL.
8. Trade is persisted to SQLite and Telegram alert is sent.
9. Positions + capital dashboard update continuously.
10. At/after 15:15, new entries are halted and square-off path is triggered.

## 5) WebSocket Handling Design

- Single broker connection via `MarketDataManager`.
- Dynamic stock subscriptions kept in memory (`symbol -> token`).
- Incoming ticks update:
  - `latest_ticks[symbol]`
  - candle builder for 1-minute OHLCV
- On exception/disconnect:
  - mark feed disconnected
  - trigger risk halt reason
  - trading loop blocks new entries until reconnected

## 6) Risk Engine Pseudocode

```python
def validate(decision, algo, capital, ctx):
    if not ctx.websocket_connected: return False, "WS disconnected"
    if capital.available_balance < 1000: return False, "Low balance"
    if ctx.global_daily_loss <= -ctx.global_max_daily_loss: return False, "Global loss reached"
    if ctx.global_open_positions >= ctx.global_max_open_positions: return False, "Open pos limit"
    if ctx.open_positions_by_algo[algo.name] >= algo.max_open_trades: return False, "Algo concurrent limit"
    if ctx.trades_by_algo[algo.name] >= algo.max_trades_per_day: return False, "Algo trades/day limit"
    if ctx.algo_pnl[algo.name] <= -algo.max_daily_loss: return False, "Algo daily loss reached"
    order_cost = decision.quantity * decision.ltp
    if order_cost > algo.capital_per_trade: return False, "Capital/trade exceeded"
    if order_cost > capital.free_margin: return False, "Insufficient margin"
    return True, "OK"
```

## 7) Order Placement Pseudocode

```python
async def execute_trade(decision):
    dedupe_key = f"{algo}:{symbol}:{minute_bucket}"
    if dedupe_key in seen: raise DuplicateOrder

    entry_payload = {
      "order_type": "LIMIT", "product": "INTRADAY",
      "symbol": decision.symbol, "side": "BUY",
      "qty": decision.quantity, "price": decision.ltp
    }

    entry = retry_3x(broker.place_limit_order, entry_payload)
    assert entry.success

    sl_payload = {**entry_payload, "trigger_price": decision.stoploss_price, "price": decision.stoploss_price}
    sl = retry_3x(broker.place_stoploss_order, sl_payload)
    assert sl.success

    persist_trade(entry, sl)
    telegram_alert("ENTRY ...")
```

## 8) UI Component Structure

- `Capital Dashboard` (balance, used/free margin, pnl, trading enabled/warning)
- `Stock Manager` (add/remove symbol-token)
- `Algo Config Panel` (JSON config for per-algo parameters)
- `Algo List` (active + paused state)
- `Open Trades` (entry, SL, target, status, pnl)
- `Manual Exit` exposed through API (can be wired to button)

(No extra styling included.)

## 9) Error Handling Flow

- **WebSocket disconnect** → `market_data.connected=False` → risk engine blocks entries.
- **Broker API error** → execution retries 3 times; on failure logs `system_events` and raises halt condition.
- **Order SL failure** → trade marked error path; alert is sent for intervention.
- **Insufficient margin/balance** → risk reject; shown on capital endpoint warning.
- **Duplicate order** → blocked by in-memory dedupe key.

## 10) Daily Reset Logic

- At day rollover:
  - mark old ledgers non-trading.
  - recalculate/initialize today ledger from fresh balance.
- At 15:15:
  - stop new entries.
  - flag open trades for force exit process.
- Ensure no overnight positions by running square-off workflow before market close.

## Run Locally

```bash
cd trading_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

## Extensibility for Kite

- Add `app/brokers/kite.py` implementing `BrokerBase` methods.
- Switch `settings.broker_name = "kite"`.
- No changes required in risk/strategy/execution modules.
