from collections import defaultdict

from app.models import AlgoConfig


class AlgoManager:
    def __init__(self):
        self.algos: dict[str, AlgoConfig] = {}
        self.paused: set[str] = set()
        self.trades_by_algo = defaultdict(int)
        self.open_positions_by_algo = defaultdict(int)
        self.algo_pnl = defaultdict(float)

    def add(self, config: AlgoConfig):
        self.algos[config.name] = config

    def toggle(self, name: str, pause: bool):
        if pause:
            self.paused.add(name)
        else:
            self.paused.discard(name)

    def list(self):
        return [{"name": k, "paused": k in self.paused, **v.model_dump()} for k, v in self.algos.items()]
