import inspect
from collections.abc import Callable
from contextlib import asynccontextmanager
from inspect import isawaitable
from typing import Any, AsyncContextManager, AsyncGenerator, AsyncIterator


def _wrap_async_gen(agen: AsyncGenerator):
    @asynccontextmanager
    async def wrapper():
        try:
            yield await agen.__anext__()
        except StopAsyncIteration:
            raise RuntimeError("Async generator didn't yield any value")

        try:
            await agen.__anext__()
        except StopAsyncIteration:
            pass
        else:
            raise RuntimeError("Async generator yielded more than one value")

    return wrapper()


class Dependency:
    def __init__(self, func: Callable[..., Any] | AsyncContextManager | AsyncGenerator, *, use_cache=True):
        self.func = func
        self.use_cache = use_cache

    @property
    def signature(self) -> inspect.Signature:
        return inspect.signature(self.func)

    def __call__(self, *args, **kwargs):
        res = self.func(*args, **kwargs)

        if isinstance(res, AsyncContextManager):
            return res

        if isinstance(res, (AsyncGenerator, AsyncIterator)):
            return _wrap_async_gen(res)

        @asynccontextmanager
        async def wrapper():
            if isawaitable(res):
                value = await res
            else:
                value = res
            yield value

        return wrapper()

    def __hash__(self):
        return hash(self.func)
