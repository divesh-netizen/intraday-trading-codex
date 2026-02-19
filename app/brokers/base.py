from abc import ABC, abstractmethod
from typing import Callable


class BrokerBase(ABC):
    name: str

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_balance(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def validate_token(self, symbol: str, token: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def place_limit_order(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def place_stoploss_order(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def exit_position(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def subscribe_ticks(self, subscriptions: list[dict], on_tick: Callable[[dict], None]) -> None:
        raise NotImplementedError
