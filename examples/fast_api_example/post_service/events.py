from dispytch import EventBase


class PostCreatedEvent(EventBase):
    __topic__ = "post_events"
    __event_type__ = "post_created"

    title: str
    content: str
