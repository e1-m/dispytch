from contextlib import asynccontextmanager
from typing import Callable, Any

from dispytch.di.builder import get_dependency_tree
from dispytch.di.models import EventHandlerContext


@asynccontextmanager
async def solve_dependencies(func: Callable[..., Any], ctx: EventHandlerContext = None):
    tree = get_dependency_tree(func)
    async with tree.resolve(ctx) as deps:
        yield deps
