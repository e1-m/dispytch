from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional


@dataclass(frozen=True)
class Backend:
    name: str
    emitter: Any
    listener: Any
    subscription: Any
    route: Any
    wildcard_subscription: Optional[Any] = None
    get_committed_offset: Optional[Callable[[], Awaitable[int]]] = None
