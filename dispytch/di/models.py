from dataclasses import dataclass


@dataclass
class Event[Body]:
    topic: str
    type: str
    body: Body


@dataclass
class EventHandlerContext:
    event: dict
