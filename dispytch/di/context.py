from dataclasses import dataclass

from dispytch.di.event import Event


@dataclass
class DIContext:
    event: dict
    subscription_pattern: tuple[str, ...]
    actual_event_route: tuple[str, ...]
