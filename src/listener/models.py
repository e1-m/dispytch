from typing import Callable, Any

from pydantic import BaseModel


class Handler:
    def __init__(self, func: Callable[..., Any]):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Event(BaseModel):
    topic: str
    type: str
    body: dict
