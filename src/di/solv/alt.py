from contextlib import AsyncExitStack
from typing import Callable, Any

from src.di.dependency import Dependency
from src.di.exc import CyclicDependencyError
from src.di.models import EventHandlerContext
from src.di.solv.extractor import get_dependencies


async def solve_dependencies_dfs(func: Callable[..., Any],
                                 stack: AsyncExitStack,
                                 resolved: dict[int, Dependency],
                                 resolving: set[int], *,
                                 ctx: EventHandlerContext) -> dict[str, Any]:
    results = {}

    if not (dependencies := get_dependencies(func)):
        return results

    for param_name, dependency in dependencies.items():
        if dependency.use_cache and hash(dependency) in resolved:
            results[param_name] = resolved[hash(dependency)]
            continue

        if hash(dependency) in resolving:
            raise CyclicDependencyError(f"Dependency cycle detected: {dependency}")

        resolving.add(hash(dependency))
        sub_deps = await solve_dependencies_dfs(dependency.func, stack, resolved, resolving, ctx=ctx)
        resolving.remove(hash(dependency))

        value = await stack.enter_async_context(dependency(**sub_deps, ctx=ctx))

        if dependency.use_cache:
            resolved[hash(dependency)] = value

        results[param_name] = value

    return results
