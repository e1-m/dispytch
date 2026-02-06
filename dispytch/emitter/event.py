from typing import Optional

from pydantic import BaseModel
from dispytch.emitter.producer import EventRoute


class EventBase(BaseModel):
    __backend_config__: Optional[BaseModel] = None
    __route__: Optional[EventRoute] = None
