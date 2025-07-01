from functools import lru_cache
from typing import Callable, Any

from src.di.exc import CyclicDependencyError
from src.di.solv.extractor import extract_dependencies
from src.di.solv.tree import DependencyTree, DependencyNode, ChildNode


@lru_cache
def get_dependency_tree(func: Callable[..., Any]) -> DependencyTree:
    return DependencyTree(_build_dependency_branches(func, {}, set()))


def _build_dependency_branches(func: Callable[..., Any],
                               resolved: dict[int, DependencyNode],
                               resolving: set[int]) -> list[ChildNode]:
    children = []

    if not (dependencies := extract_dependencies(func)):
        return children

    for param_name, dependency in dependencies.items():
        if dependency.use_cache and hash(dependency) in resolved:
            children.append(ChildNode(param_name, resolved[hash(dependency)]))
            continue

        if hash(dependency) in resolving:
            raise CyclicDependencyError(f"Dependency cycle detected: {dependency}")

        resolving.add(hash(dependency))
        current_node = DependencyNode(dependency, _build_dependency_branches(dependency.func, resolved, resolving))
        resolving.remove(hash(dependency))

        if dependency.use_cache:
            resolved[hash(dependency)] = current_node

        children.append(ChildNode(param_name, current_node))

    return children
