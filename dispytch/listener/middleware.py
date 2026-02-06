from typing import Protocol, Callable, Awaitable, Any

from pydantic import BaseModel


class Middleware(Protocol):
    async def dispatch(self, event: BaseModel, call_next: Callable[..., Awaitable[Any]]): ...
