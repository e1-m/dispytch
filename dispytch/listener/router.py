from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any

from dispytch import EventSubscription
from dispytch.listener.middleware import Middleware


@dataclass
class HandlerData:
    func: Callable[..., Any]
    middlewares: list[Middleware]


class Router:
    def __init__(
            self,
            middlewares: list[Middleware] = None,
    ):
        self._middlewares = middlewares if middlewares else []
        self._handlers: dict[EventSubscription, list[HandlerData]] = defaultdict(list)

    def handler(
            self,
            subscription: EventSubscription,
            *,
            middlewares: list[Middleware] = None,
    ):
        middlewares = middlewares if middlewares else []

        def decorator(callback):
            handlers = self._handlers[subscription]

            handlers.append(
                HandlerData(
                    func=callback,
                    middlewares=self._middlewares + middlewares
                )
            )
            return callback

        return decorator

    def get_handlers(self, subscription: EventSubscription) -> list[HandlerData]:
        return self._handlers[subscription]

    def get_subscriptions(self) -> list[EventSubscription]:
        return list(self._handlers.keys())
