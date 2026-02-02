import inspect
from typing import Callable, Any, get_origin, Annotated, get_args, get_type_hints
from dataclasses import asdict

from pydantic import BaseModel, TypeAdapter, ValidationError

from dispytch.di.dependency import Dependency
from dispytch.di.event import Event
from dispytch.di.context import EventHandlerContext
from dispytch.di.subscription_param import SubscriptionParam


def extract_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    dependencies = _extract_user_defined_dependencies(func)
    dependencies.update(_extract_event_dependencies(func))
    dependencies.update(_extract_subscription_param_dependencies(func))

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
            deps[name] = _make_event_dependency(body_model=event_body_model)

        elif annotation is Event:
            deps[name] = _make_event_dependency(body_model=dict)

    return deps


def _make_event_dependency(body_model):
    def context_to_event(ctx: EventHandlerContext) -> Event:
        event_data = asdict(ctx.event)
        body = event_data.pop('body')

        return Event(body=body_model(**body), **event_data)

    return Dependency(context_to_event)


def _extract_subscription_param_dependencies(func: Callable[..., Any]) -> dict[str, Dependency]:
    deps = {}

    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        default = param.default
        annotation = param.annotation

        if isinstance(default, SubscriptionParam):
            deps[name] = _make_subscription_param_dependency(
                segment_name=default.validation_alias or default.alias or name,
                field=Annotated[annotation, default]
            )

        elif get_origin(annotation) is Annotated:
            base_type, *metadata = get_args(annotation)

            for meta in metadata:
                if isinstance(meta, SubscriptionParam):
                    deps[name] = _make_subscription_param_dependency(
                        segment_name=meta.validation_alias or meta.alias or name,
                        field=annotation
                    )
                    break
                elif meta is SubscriptionParam:
                    deps[name] = _make_subscription_param_dependency(
                        segment_name=name,
                        field=base_type
                    )
                    break

    return deps


def _make_subscription_param_dependency(segment_name, field):
    def extract_field_from_subscription_pattern(ctx: EventHandlerContext):
        value = _extract_param(
            actual=ctx.actual_event_route,
            pattern=ctx.subscription_pattern,
            segment_name=segment_name
        )

        return _validate_field(value, field)

    return Dependency(extract_field_from_subscription_pattern)


def _extract_param(actual: tuple[str, ...],
                   pattern: tuple[str, ...],
                   segment_name: str) -> str:
    try:
        index = pattern.index(f"{{{segment_name}}}")
        value = actual[index]

        return value
    except ValueError:
        raise ValueError(f"Receiver expected to get a value under '{segment_name}' segment, "
                         f"but no segment with such name was found in topic pattern '{pattern}'")


def _validate_field(
        value: Any,
        field: type
) -> Any:
    try:
        adapter = TypeAdapter(field)
        return adapter.validate_python(value)
    except ValidationError as e:
        raise ValueError(f"Value '{value}' does not match the expected type constrains:\n "
                         f"{e}")
    except TypeError:
        raise TypeError(f"Type '{field}' has conflicting type annotations or is not a valid type for validation.")
