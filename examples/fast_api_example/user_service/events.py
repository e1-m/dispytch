from dispytch import EventBase


class UserCreatedEvent(EventBase):
    __topic__ = "user_events"
    __event_type__ = "user_created"

    name: str
