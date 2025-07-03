import asyncio
import logging
from collections import defaultdict

from dispytch.di.models import EventHandlerContext
from dispytch.di.solver import solve_dependencies
from dispytch.listener.consumer import Consumer, Event as ConsumerEvent
from dispytch.listener.handler import Handler


class EventListener:
    def __init__(self, consumer: Consumer):
        self.tasks = set()
        self.consumer = consumer
        self.handlers = defaultdict(dict[str, Handler])

    async def listen(self):
        async for event in self.consumer.listen():
            task = asyncio.create_task(self._handle_event(event))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

        if self.tasks:
            await asyncio.wait(self.tasks)

    async def _handle_event(self, event: ConsumerEvent):
        try:
            await self._trigger_callback_with_injected_dependencies(event)
            await self.consumer.ack(event)
        except KeyError:
            logging.info(f'No handler for event: {event.type}')
        except Exception as e:
            logging.error(f"Exception in {event.type} event handler: \n{e}")

    async def _trigger_callback_with_injected_dependencies(self, event: ConsumerEvent):
        handler = self.handlers[event.topic][event.type]

        async with solve_dependencies(handler.func,
                                      EventHandlerContext(
                                          event=event.model_dump(exclude={'id'})
                                      )) as deps:
            await handler(**deps)

    def handler(self, *, topic, event, retries=0, retry_on=None):
        def decorator(callback):
            self.handlers[topic][event] = Handler(callback, retries, retry_on)
            return callback

        return decorator
