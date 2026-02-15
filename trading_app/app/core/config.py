from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Intraday Equity Trader"
    database_url: str = "sqlite:///./trading_app.db"
    broker_name: str = "angel"
    broker_retry_attempts: int = 3
    min_balance_threshold: float = 1000.0
    auto_square_off_time: str = "15:15"
    market_open_time: str = "09:15"
    market_close_time: str = "15:30"
    telegram_token: str | None = None
    telegram_chat_id: str | None = None


settings = Settings()
