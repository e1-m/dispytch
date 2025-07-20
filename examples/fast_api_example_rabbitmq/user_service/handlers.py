import logging

from dispytch import HandlerGroup, Event

from user_service.config import event_handling_config

logger = logging.getLogger(__name__)

post_events = HandlerGroup(
    event_handling_config.POST_EVENTS_TOPIC
)


@post_events.handler(event="post_created")
def handle_post_created(event: Event):
    logger.info(f"Got post_created event {event.id}: {event.body}")
