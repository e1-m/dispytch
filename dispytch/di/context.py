from dataclasses import dataclass

from dispytch.di.event import Event


@dataclass
class EventHandlerContext:
    event: Event[dict]
    subscription_segments: tuple[str, ...]
    segment_delimiter: str
