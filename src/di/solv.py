import asyncio
import inspect
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Callable, Any, get_origin, Annotated, get_args, get_type_hints

from pydantic import BaseModel

from src.di.dependency import Dependency
from src.di.exc import CyclicDependencyError
from src.di.models import EventHandlerContext, Event


@asynccontextmanager
async def get_solved_dependencies(func: Callable[..., Any], ctx: EventHandlerContext = None):
    async with AsyncExitStack() as stack:  # noqa
        yield await _solve_dependencies(func, stack, {}, set(), ctx=ctx if ctx else EventHandlerContext(event={}))


def _get_user_defined_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
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
    deps = {}
    for name, annotation in get_type_hints(func).items():
        if get_origin(annotation) is Event:
            event_body_model, *_ = get_args(annotation)
            if not issubclass(event_body_model, BaseModel):
                raise TypeError(f"Event body model must be a subclass of pydantic.BaseModel, got {event_body_model}")

        elif annotation is Event:
            event_body_model = dict

        else:
            continue

        metadata = ctx.event.copy()
        body = metadata.pop('body')

        event = Event(body=event_body_model(**body), **metadata)
        deps[name] = Dependency(lambda e=event: e)

    return deps


def _get_dependencies(func: Callable[..., Any], ctx: EventHandlerContext) -> dict[str, Dependency]:
    dependencies = _get_user_defined_dependencies(func)
    dependencies.update(_get_event_requests_as_dependencies(func, ctx))

    return dependencies


class DependencyNode:
    def __init__(self,
                 dependency: Dependency,
                 children: list['ChildNode']):
        self.dependency = dependency
        self.children = children
        self._task = None

    async def resolve(self, stack: AsyncExitStack):
        tasks = [asyncio.create_task(child.dependency.resolve(stack)) for child in self.children]

        resolved = await asyncio.gather(*tasks)

        kwargs = {child.param_name: res
                  for child, res
                  in zip(self.children, resolved)}

        if self._task is None:
            self._task = asyncio.create_task(
                stack.enter_async_context(
                    self.dependency(**kwargs)
                ))

        return await self._task


class ChildNode:
    def __init__(self, param_name: str, dependency: DependencyNode):
        self.param_name = param_name
        self.dependency = dependency


class DependencyTree:
    def __init__(self, root_nodes: list[ChildNode], stack: AsyncExitStack):
        self.root_nodes = root_nodes
        self.stack = stack

    @asynccontextmanager
    async def resolve(self):
        async with self.stack:
            tasks = [asyncio.create_task(node.dependency.resolve(self.stack)) for node in self.root_nodes]

            resolved = await asyncio.gather(*tasks)

            yield {node.param_name: dep for node, dep in zip(self.root_nodes, resolved)}

async def _solve_dependencies(func: Callable[..., Any],
                              stack: AsyncExitStack,
                              resolved: dict[int, Any],
                              resolving: set[int], *,
                              ctx: EventHandlerContext) -> dict[str, Any]:
    results = {}

    if not (dependencies := _get_dependencies(func, ctx)):
        return results

    for param_name, dependency in dependencies.items():
        if dependency.use_cache and hash(dependency) in resolved:
            results[param_name] = resolved[hash(dependency)]
            continue

        if hash(dependency) in resolving:
            raise CyclicDependencyError(f"Dependency cycle detected: {dependency}")

        resolving.add(hash(dependency))
        sub_deps = await _solve_dependencies(dependency.func, stack, resolved, resolving, ctx=ctx)
        resolving.remove(hash(dependency))

        value = await stack.enter_async_context(dependency(**sub_deps))

        if dependency.use_cache:
            resolved[hash(dependency)] = value

        results[param_name] = value

    return results
