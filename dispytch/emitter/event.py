from typing import Optional

from pydantic import BaseModel
from dispytch.emitter.producer import EventRoute, BackendConfig


class EventBase(BaseModel):
    __route__: EventRoute
    __backend_config__: Optional[BackendConfig] = None
