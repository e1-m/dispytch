import inspect
from collections.abc import Callable
from contextlib import asynccontextmanager
from inspect import isawaitable
from typing import Any, AsyncContextManager, AsyncGenerator, AsyncIterator, Generator, Iterator, ContextManager

from src.di.exc import InvalidGeneratorError


def _get_async_cm_from_iterator(gen: AsyncIterator | Iterator):
    @asynccontextmanager
    async def wrapper():
        try:
            yield await gen.__anext__() if hasattr(gen, "__anext__") else next(gen)
        except (StopAsyncIteration, StopIteration):
            raise InvalidGeneratorError("Generator didn't yield any value")

        try:
            await gen.__anext__() if hasattr(gen, "__anext__") else next(gen)
        except (StopAsyncIteration, StopIteration):
            pass
        else:
            raise InvalidGeneratorError("Generator yielded more than one value")

    return wrapper()


def _get_async_cm_from_cm(sync_cm: ContextManager[Any]):
    @asynccontextmanager
    async def wrapper():
        with sync_cm as value:
            yield value

    return wrapper()


DependencyFuncType = Callable[
    ..., Any | AsyncContextManager | ContextManager | AsyncGenerator | Generator | AsyncIterator | Iterator]


class Dependency:
    def __init__(self, func: DependencyFuncType, *, use_cache=True):
        self.func = func
        self.use_cache = use_cache

    @property
    def signature(self) -> inspect.Signature:
        return inspect.signature(self.func)

    def __call__(self, *args, **kwargs) -> AsyncContextManager[Any]:
        sig = inspect.signature(self.func)
        accepted_params = sig.parameters.keys()
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted_params}

        res = self.func(*args, **filtered_kwargs)

        if isinstance(res, AsyncContextManager):
            return res

        if isinstance(res, ContextManager):
            return _get_async_cm_from_cm(res)

        if isinstance(res, (AsyncIterator, Iterator)):
            return _get_async_cm_from_iterator(res)

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
