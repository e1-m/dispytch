from functools import lru_cache
from typing import Callable, Any

from dispytch.di.exc import CyclicDependencyError
from dispytch.di.extractor import extract_dependencies

from dispytch.di.tree import DependencyNode, ChildNode, DependencyTree


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
