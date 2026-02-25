import logging

from pydantic import BaseModel

from dispytch import Router, Event
from dispytch.rabbitmq import RabbitMQEventSubscription

logger = logging.getLogger(__name__)

post_events = Router()


class PostCreatedEvent(BaseModel):
    title: str
    content: str


@post_events.handler(RabbitMQEventSubscription(routing_key="post.created"))
def handle_post_created(event: Event[PostCreatedEvent]):
    logger.info(f"Got post.created event. Title: {event.title}")
