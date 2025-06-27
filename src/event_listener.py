import asyncio
import logging
from collections import defaultdict
from contextlib import AsyncExitStack
from typing import Callable, Any, AsyncContextManager

from src.consumer.consumer import Consumer
from src.schemas.event import Event


class EventListener:
    def __init__(self, consumer: Consumer):
        self.consumer = consumer
        self.callbacks = defaultdict(dict)
        self.dependencies: dict[str, dict[str, Callable[..., AsyncContextManager[Any]]]] = {}

    async def listen(self):
        async for event in self.consumer.listen():
            asyncio.create_task(self._handle_event(event))

    async def _handle_event(self, event: Event):
        try:
            await self._trigger_callback_with_injected_dependencies(event)
        except KeyError:
            logging.info(f'No handler for event: {event.type}')
        except Exception as e:
            logging.error(f"Exception in {event.type} event handler: \n{e}")

    async def _trigger_callback_with_injected_dependencies(self, event: Event):
        async with AsyncExitStack() as stack:
            kwargs = {
                key: await stack.enter_async_context(dep()) for key, dep in
                self.dependencies[event.topic + event.type].items()
            }

            await self.callbacks[event.topic][event.type](event.body, **kwargs)

    def handler(self, *, topic, event, inject: dict[str, Callable[..., AsyncContextManager[Any]]] = None):
        def decorator(callback):
            self.callbacks[topic][event] = callback
            self.dependencies[topic + event] = inject or {}

        return decorator
