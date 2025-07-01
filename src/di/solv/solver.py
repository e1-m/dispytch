from contextlib import asynccontextmanager, AsyncExitStack
from typing import Callable, Any

from src.di.models import EventHandlerContext
from src.di.solv.alt import solve_dependencies_dfs
from src.di.solv.builder import get_dependency_tree


@asynccontextmanager
async def solve_dependencies(func: Callable[..., Any], ctx: EventHandlerContext = None):
    tree = get_dependency_tree(func)
    async with tree.resolve(ctx) as deps:
        yield deps


@asynccontextmanager
async def solve_dependencies_alternative(func: Callable[..., Any], ctx: EventHandlerContext = None):
    async with AsyncExitStack() as stack:  # noqa
        yield await solve_dependencies_dfs(func, stack, {}, set(), ctx=ctx)
