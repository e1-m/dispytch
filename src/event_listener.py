import asyncio
import logging
from collections import defaultdict

from src.consumer.consumer import Consumer
from src.di.solv import get_solved_dependencies
from src.schemas.event import Event


class EventListener:
    def __init__(self, consumer: Consumer):
        self.consumer = consumer
        self.callbacks = defaultdict(dict)

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
        callback = self.callbacks[event.topic][event.type]

        async with get_solved_dependencies(callback) as deps:
            await callback(event.body, **deps)

    def handler(self, *, topic, event):
        def decorator(callback):
            self.callbacks[topic][event] = callback

        return decorator
