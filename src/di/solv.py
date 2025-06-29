import inspect
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Callable, Any, get_origin, Annotated, get_args, Type, get_type_hints

from pydantic import BaseModel

from src.di.dependency import Dependency
from src.di.exc import CyclicDependencyError
from src.di.models import EventHandlerContext, Event


@asynccontextmanager
async def get_solved_dependencies(func: Callable[..., Any], ctx: EventHandlerContext = None):
    async with AsyncExitStack() as stack:  # noqa
        yield await _solve_dependencies(func, stack, {}, set(), ctx=ctx if ctx else EventHandlerContext(event={}))


def _get_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    deps = {}

    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        default = param.default
        if isinstance(default, Dependency):
            deps[name] = default
            continue

        annotation = param.annotation
        if get_origin(annotation) is Annotated:
            base_type, *metadata = get_args(annotation)

            for meta in metadata:
                if isinstance(meta, Dependency):
                    deps[name] = meta
                    break

    return deps


def _get_event_requests_as_dependencies(func: Callable[..., Any], ctx: EventHandlerContext) -> dict[str, Dependency]:
    event_requests = {}
    for name, annotation in get_type_hints(func).items():

        if get_origin(annotation) is Event:
            event_body_model, *_ = get_args(annotation)
            if issubclass(event_body_model, BaseModel):
                event_data = ctx.event.copy()
                event_data.pop('body', None)

                event = Event(body=event_body_model(**ctx.event['body']), **event_data)
                event_requests[name] = Dependency(lambda e=event: e)
    return event_requests


async def _solve_dependencies(func: Callable[..., Any],
                              stack: AsyncExitStack,
                              resolved: dict[int, Any],
                              resolving: set[int], *,
                              ctx: EventHandlerContext) -> dict[str, Any]:
    results = {}

    dependencies = _get_dependencies(func)
    dependencies.update(_get_event_requests_as_dependencies(func, ctx))

    if not dependencies:
        return results

    for key, dep in dependencies.items():
        if dep.use_cache and hash(dep) in resolved:
            results[key] = resolved[hash(dep)]
            continue

        if hash(dep) in resolving:
            raise CyclicDependencyError(f"Dependency cycle detected: {dep}")

        resolving.add(hash(dep))
        sub_deps = await _solve_dependencies(dep.func, stack, resolved, resolving, ctx=ctx)
        resolving.remove(hash(dep))

        ctx = dep(**sub_deps)

        value = await stack.enter_async_context(ctx)

        if dep.use_cache:
            resolved[hash(dep)] = value

        results[key] = value

    return results
