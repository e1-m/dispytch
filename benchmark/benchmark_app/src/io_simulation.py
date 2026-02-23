import asyncio
import logging
import random

from pydantic import BaseModel

from dispytch import Router, Event
from dispytch.kafka import KafkaEventSubscription

logger = logging.getLogger(__name__)

router = Router()


class BenchmarkEvent(BaseModel):
    id: str
    payload: str


@router.handler(KafkaEventSubscription(topic='benchmark_events'))
async def handle_event(event: Event[BenchmarkEvent]):
    await asyncio.sleep(random.uniform(0.1, 0.7))
