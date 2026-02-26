from dispytch import EventBase
from dispytch.rabbitmq import RabbitMQEventRoute


class PostCreatedEvent(EventBase):
    __route__ = RabbitMQEventRoute(
        exchange="post.events",
        routing_key="post.created"
    )

    title: str
    content: str
