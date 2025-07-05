from dataclasses import dataclass


@dataclass
class Event[Body]:
    id: str
    topic: str
    type: str
    body: Body


@dataclass
class EventHandlerContext:
    event: dict
