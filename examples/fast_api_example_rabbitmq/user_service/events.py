from dispytch import EventBase
from dispytch.rabbitmq import RabbitMQEventRoute


class UserCreatedEvent(EventBase):
    __route__ = RabbitMQEventRoute(
        exchange="user.events",
        routing_key="user.created"
    )

    name: str
