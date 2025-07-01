import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from src.di.dependency import Dependency
from src.di.models import EventHandlerContext


class DependencyNode:
    def __init__(self,
                 dependency: Dependency,
                 children: list['ChildNode']):
        self.dependency = dependency
        self.children = children
        self._task = None

    async def resolve(self, stack: AsyncExitStack, ctx: EventHandlerContext):
        tasks = [asyncio.create_task(child.dependency.resolve(stack, ctx)) for child in self.children]

        resolved = await asyncio.gather(*tasks)

        kwargs = {child.param_name: res
                  for child, res
                  in zip(self.children, resolved)}

        if self._task is None:
            self._task = asyncio.create_task(
                stack.enter_async_context(
                    self.dependency(**kwargs, ctx=ctx)
                ))

        return await self._task


class ChildNode:
    def __init__(self, param_name: str, dependency: DependencyNode):
        self.param_name = param_name
        self.dependency = dependency


class DependencyTree:
    def __init__(self, root_nodes: list[ChildNode]):
        self.root_nodes = root_nodes

    @asynccontextmanager
    async def resolve(self, ctx: EventHandlerContext):
        async with AsyncExitStack() as stack:  # noqa
            tasks = [asyncio.create_task(node.dependency.resolve(stack, ctx)) for node in self.root_nodes]

            resolved = await asyncio.gather(*tasks)

            yield {node.param_name: dep for node, dep in zip(self.root_nodes, resolved)}
