import asyncio
from inspect import isawaitable

import time


async def assert_eventually(assertion, timeout: float = 1.0, interval: float = 0.05):
    deadline = time.monotonic() + timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            res = assertion()
            if isawaitable(res):
                await res
            return
        except AssertionError as e:
            last_err = e
            await asyncio.sleep(interval)
    raise last_err or AssertionError("Condition not met in time")
