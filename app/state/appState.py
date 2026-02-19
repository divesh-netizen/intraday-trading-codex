from app.brokers.factory import get_broker
from app.core.config import settings
from app.data.market_data import MarketDataManager
from app.engine.algo_manager import AlgoManager
from app.engine.execution import ExecutionEngine
from app.engine.risk import RiskEngine


class AppState:
    def __init__(self):
        self.broker = get_broker(settings.broker_name)
        self.market_data = MarketDataManager(self.broker)
        self.algo_manager = AlgoManager()
        self.risk_engine = RiskEngine()
        self.execution_engine = ExecutionEngine(self.broker)
        self.global_max_open_positions = 2
        self.global_max_daily_loss = 3000


state = AppState()
