from contextlib import asynccontextmanager
from typing import Callable, Any

from dispytch.di.builder import get_dependency_tree, get_internal_dependencies_tree
from dispytch.di.context import DIContext


# This is a bridge for tests. Shouldn't be used anywhere in the source code except tests
@asynccontextmanager
async def solve_dependencies(func: Callable[..., Any], ctx: DIContext = None) -> dict[str, Any]:
    di = DIResolver(ctx)
    async with di.resolve(func) as deps:
        yield deps


class DIResolver:
    def __init__(self, ctx: DIContext):
        self.ctx = ctx

    @asynccontextmanager
    async def resolve(self, func: Callable[..., Any]) -> dict[str, Any]:
        tree = get_dependency_tree(func)
        async with tree.resolve(self.ctx) as deps:
            yield deps

    @asynccontextmanager
    async def resolve_internal_only(self, func: Callable[..., Any]) -> dict[str, Any]:
        tree = get_internal_dependencies_tree(func)
        async with tree.resolve(self.ctx) as deps:
            yield deps
