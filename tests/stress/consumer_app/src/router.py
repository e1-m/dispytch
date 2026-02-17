import asyncio
import logging

from pydantic import BaseModel

from dispytch import Router, Event
from dispytch.kafka import KafkaEventSubscription

logger = logging.getLogger(__name__)

router = Router()


class StressTestEvent(BaseModel):
    id: str


@router.handler(KafkaEventSubscription(topic='stress_test_events'))
async def handle_event(event: Event[StressTestEvent]):
    logger.info(f"Event with id {event.id} arrived")
    # await asyncio.sleep(0.5)
