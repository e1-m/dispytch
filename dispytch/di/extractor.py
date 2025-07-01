import inspect
from typing import Callable, Any, get_origin, Annotated, get_args, get_type_hints

from pydantic import BaseModel

from dispytch import Dependency, Event
from dispytch.di.models import EventHandlerContext


def extract_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    dependencies = _extract_user_defined_dependencies(func)
    dependencies.update(_extract_event_dependencies(func))

    return dependencies


def _extract_user_defined_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
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


def _extract_event_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    deps = {}

    hints = get_type_hints(func)
    hints.pop('return', None)

    for name, annotation in hints.items():
        if get_origin(annotation) is Event:
            event_body_model, *_ = get_args(annotation)
            if not issubclass(event_body_model, BaseModel):
                raise TypeError(f"Event body model must be a subclass of pydantic.BaseModel, got {event_body_model}")

        elif annotation is Event:
            event_body_model = dict

        else:
            continue

        def context_to_event(ctx: EventHandlerContext, model=event_body_model) -> Event:
            metadata = ctx.event.copy()
            body = metadata.pop('body')

            return Event(body=model(**body), **metadata)

        deps[name] = Dependency(context_to_event)

    return deps
