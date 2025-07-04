import asyncio
import logging
from collections import defaultdict

from dispytch.di.models import EventHandlerContext
from dispytch.di.solver import solve_dependencies
from dispytch.listener.consumer import Consumer, Event as ConsumerEvent
from dispytch.listener.handler import Handler
from dispytch.listener.handler_group import HandlerGroup


async def _call_handler_with_injected_dependencies(handler: Handler, event: ConsumerEvent):
    async with solve_dependencies(handler.func,
                                  EventHandlerContext(
                                      event=event.model_dump(exclude={'id'})
                                  )) as deps:
        try:
            await handler.handle(**deps)
        except Exception as e:
            logging.exception(f"Handler {handler.func.__name__} failed for event {event.type}: {e}")


class EventListener:
    def __init__(self, consumer: Consumer):
        self.tasks = set()
        self.consumer = consumer
        self.handlers: dict[str, dict[str, list[Handler]]] = defaultdict(lambda: defaultdict(list))

    async def listen(self):
        async for event in self.consumer.listen():
            task = asyncio.create_task(self._handle_event(event))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

        if self.tasks:
            await asyncio.wait(self.tasks)

    async def _handle_event(self, event: ConsumerEvent):
        handlers = self.handlers[event.topic][event.type]
        if not handlers:
            logging.info(f'There is not handler for topic `{event.topic}` and event type `{event.type}`')
            return

        tasks = [asyncio.create_task(
            _call_handler_with_injected_dependencies(handler, event)
        ) for handler in handlers]
        await asyncio.gather(*tasks)

        await self.consumer.ack(event)

    def handler(self, *,
                topic: str,
                event: str,
                retries: int = 0,
                retry_on: type[Exception] = None,
                retry_interval_sec: float = 1.25):
        def decorator(callback):
            self.handlers[topic][event].append(Handler(callback, retries, retry_interval_sec, retry_on))
            return callback

        return decorator

    def add_handler_group(self, group: HandlerGroup):
        for topic in group.handlers:
            for event in group.handlers[topic]:
                self.handlers[topic][event].extend(group.handlers[topic][event])
