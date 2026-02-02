from dataclasses import dataclass

from dispytch.di.event import Event


@dataclass
class EventHandlerContext:
    event: Event[dict]
    subscription_pattern: tuple[str, ...]
    actual_event_route: tuple[str, ...]
