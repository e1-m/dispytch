import asyncio
from inspect import isawaitable
from typing import Callable, Any, Sequence


class Handler:
    def __init__(self, func: Callable[..., Any],
                 retries: int = 0,
                 retry_interval_sec: int = 0,
                 retry_on: Sequence[type[Exception]] = None):
        self.retries = abs(retries)
        self.retry_on = retry_on
        self.retry_interval = abs(retry_interval_sec)
        self.func = func

    async def handle(self, *args, **kwargs):
        for attempt in range(self.retries + 1):  # noqa
            try:
                res = self.func(*args, **kwargs)
                if isawaitable(res):
                    return await res
                return res
            except Exception as e:
                should_retry = (
                        self.retry_on is None or
                        isinstance(e, tuple(self.retry_on))
                )

                if attempt == self.retries or not should_retry:
                    raise e
                await asyncio.sleep(self.retry_interval)
