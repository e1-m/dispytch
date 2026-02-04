from contextlib import asynccontextmanager
from typing import Callable, Any

from dispytch.di.builder import get_dependency_tree
from dispytch.di.context import DIContext


class DIResolver:
    def __init__(self, ctx: DIContext):
        self.ctx = ctx

    @asynccontextmanager
    async def resolve(self, func: Callable[..., Any]) -> dict[str, Any]:
        tree = get_dependency_tree(func)
        async with tree.resolve(self.ctx) as deps:
            yield deps
