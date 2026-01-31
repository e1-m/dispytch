from dataclasses import dataclass

from dispytch.di.event import Event


@dataclass
class EventHandlerContext:
    event: Event[dict]
    subscription_pattern: str
    actual_event_route: str
    route_delimiter: str
