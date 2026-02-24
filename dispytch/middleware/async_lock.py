import asyncio
from dataclasses import dataclass
from typing import Callable, Hashable

from dispytch.dispatcher.middleware import EventHandlerContext, NextCall, Middleware


@dataclass
class _SemaphoreEntry:
    semaphore: asyncio.Semaphore
    ref_count: int


class AsyncLock(Middleware):
    def __init__(
            self,
            key_extractor: Callable[[EventHandlerContext], Hashable] = None,
            concurrency_limit: int = 1
    ):
        self.key_extractor = key_extractor
        self.concurrency_limit = concurrency_limit

        self._semaphores: dict[Hashable, _SemaphoreEntry] = {}

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        key = self.key_extractor(ctx) if self.key_extractor else "__GLOBAL_LOCK__"

        if key not in self._semaphores:
            self._semaphores[key] = _SemaphoreEntry(semaphore=asyncio.Semaphore(self.concurrency_limit), ref_count=0)

        self._semaphores[key].ref_count += 1

        try:
            async with self._semaphores[key].semaphore:
                return await call_next(ctx)
        finally:
            self._semaphores[key].ref_count -= 1

            if self._semaphores[key].ref_count == 0:
                del self._semaphores[key]
