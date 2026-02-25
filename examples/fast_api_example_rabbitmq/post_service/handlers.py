import logging

from pydantic import BaseModel

from dispytch import Router, Event
from dispytch.rabbitmq import RabbitMQEventSubscription

logger = logging.getLogger(__name__)

user_events = Router()


class UserCreatedEvent(BaseModel):
    name: str


@user_events.handler(RabbitMQEventSubscription(routing_key="user.created"))
def handle_user_created(event: Event[UserCreatedEvent]):
    logger.info(f"Got user_created event. Name: {event.name}")
