from dataclasses import dataclass


@dataclass
class EventHandlerContext:
    event: dict
    topic_pattern: str
    topic_delimiter: str
