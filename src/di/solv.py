import inspect
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Callable, Any, get_origin, Annotated, get_args

from src.di.dependency import Dependency


def get_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    sig = inspect.signature(func)

    deps = {}
    for name, param in sig.parameters.items():
        annotation = param.annotation
        default = param.default

        if isinstance(default, Dependency):
            deps[name] = default
            continue

        if get_origin(annotation) is Annotated:
            base_type, *metadata = get_args(annotation)

            for meta in metadata:
                if isinstance(meta, Dependency):
                    deps[name] = meta
                    break

    return deps


@asynccontextmanager
async def get_solved_dependencies(func: Callable[..., Any]):
    async with AsyncExitStack() as stack:
        yield await _solve_dependencies(func, stack, {}, set())


async def _solve_dependencies(func: Callable[..., Any],
                              stack: AsyncExitStack,
                              resolved: dict[int, Any],
                              resolving: set[int]) -> dict[str, Any]:
    results = {}

    if not (dependencies := get_dependencies(func)):
        return results

    for key, dep in dependencies.items():
        if dep.use_cache and hash(dep) in resolved:
            results[key] = resolved[hash(dep)]
            continue

        if hash(dep) in resolving:
            raise RuntimeError(f"Dependency cycle detected: {dep.func.__name__}")

        resolving.add(hash(dep))
        sub_deps = await _solve_dependencies(dep.func, stack, resolved, resolving)
        resolving.remove(hash(dep))

        ctx = dep(**sub_deps)

        value = await stack.enter_async_context(ctx)

        resolved[hash(dep)] = value
        results[key] = value

    return results
