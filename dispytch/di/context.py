from dataclasses import dataclass

from dispytch.di.event import Event


@dataclass
class EventHandlerContext:
    event: Event[dict]
    topic_pattern: str
    topic_delimiter: str
