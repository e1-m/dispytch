import asyncio
import logging
import random
from typing import Annotated

from pydantic import BaseModel

from dispytch import Router, Event, Dependency
from dispytch.kafka import KafkaEventSubscription

from .config import config

logger = logging.getLogger(__name__)

router = Router()


class BenchmarkEvent(BaseModel):
    id: str
    payload: str


semaphore = asyncio.Semaphore(config.MAX_RESOURCE_POOL_SIZE)


async def get_resource():
    async with semaphore:
        yield "resource"


@router.handler(KafkaEventSubscription(topic='benchmark_events'))
async def handle_event(event: Event[BenchmarkEvent], resource: Annotated[str, Dependency(get_resource)]):
    await asyncio.sleep(
        random.uniform(
            config.MIN_PROCESSING_TIME_MS / 1000,
            config.MAX_PROCESSING_TIME_SECONDS / 1000
        )
    )
