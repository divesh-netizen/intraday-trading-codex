from app.brokers.angel import AngelBroker
from app.brokers.base import BrokerBase


def get_broker(name: str) -> BrokerBase:
    if name == "angel":
        return AngelBroker()
    raise ValueError(f"Unsupported broker: {name}")
