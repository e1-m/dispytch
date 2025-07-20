import logging

from dispytch import HandlerGroup, Event

from post_service.config import event_handling_config

logger = logging.getLogger(__name__)

user_events = HandlerGroup(
    event_handling_config.USER_EVENTS_TOPIC
)


@user_events.handler(event="user_created")
def handle_user_created(event: Event):
    logger.info(f"Got user_created event {event.id}: {event.body}")
