import asyncio
import logging
from contextlib import asynccontextmanager

from dispytch import EventDispatcher
from dispytch.rabbitmq import RabbitMQConsumer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .handlers import post_events
from .rabbitmq_setup import init_rabbit_mq
from .router import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq = await init_rabbit_mq()

    app.state.rabbitmq = rabbitmq

    consumer = RabbitMQConsumer(
        rabbitmq.post_queue,
    )

    await consumer.start()

    listener = EventDispatcher(consumer)

    listener.add_router(post_events)

    asyncio.create_task(listener.start())

    yield

    await rabbitmq.connection.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
