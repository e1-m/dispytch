from contextlib import asynccontextmanager
from typing import Callable, Any

from src.di.models import EventHandlerContext
from src.di.solv.builder import get_dependency_tree


@asynccontextmanager
async def solve_dependencies(func: Callable[..., Any], ctx: EventHandlerContext = None):
    tree = get_dependency_tree(func)
    async with tree.resolve(ctx) as deps:
        yield deps
