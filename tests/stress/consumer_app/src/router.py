import asyncio
import logging

from pydantic import BaseModel

from dispytch import Router, Event
from dispytch.kafka import KafkaEventSubscription

from .middleware import EventsInProgressMiddleware

logger = logging.getLogger(__name__)

router = Router(
    middlewares=[EventsInProgressMiddleware()]
)


class StressTestEvent(BaseModel):
    id: str


@router.handler(KafkaEventSubscription(topic='stress_test_events'))
async def handle_event(event: Event[StressTestEvent]):
    await asyncio.sleep(1)
