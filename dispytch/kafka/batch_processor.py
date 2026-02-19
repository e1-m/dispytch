import asyncio
from typing import Awaitable, Callable
import logging

logger = logging.getLogger(__name__)


class BatchProcessor[T]:
    def __init__(self, handler: Callable[[list[T]], Awaitable[None]], batch_timeout_ms: int, batch_size: int):
        self.handler = handler
        self.batch_timeout = batch_timeout_ms / 1000.0
        self.max_batch_size = batch_size

        self._batch: list[T] = []
        self._timer_task: asyncio.Task | None = None

    async def add(self, item: T):
        self._batch.append(item)

        if len(self._batch) >= self.max_batch_size:
            await self._commit_batch(reason="size")

        elif self._timer_task is None:
            self._timer_task = asyncio.create_task(self._start_timer())

    async def _start_timer(self):
        try:
            await asyncio.sleep(self.batch_timeout)
            await self._commit_batch(reason="time")
        except asyncio.CancelledError:
            pass

    async def _commit_batch(self, reason: str):
        if not self._batch:
            return

        if reason == "size" and self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

        elif reason == "time":
            self._timer_task = None

        batch, self._batch = self._batch, []
        await self.handler(batch)
