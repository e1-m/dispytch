import asyncio
import logging
from contextlib import asynccontextmanager

from dispytch import EventListener
from dispytch.rabbitmq import RabbitMQConsumer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from post_service.config import settings
from post_service.handlers import user_events
from post_service.rabbitmq_setup import init_rabbit_mq
from post_service.router import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq = await init_rabbit_mq()

    app.state.rabbitmq = rabbitmq

    listener = EventListener(
        RabbitMQConsumer(
            rabbitmq.user_queue,
        )
    )

    listener.add_handler_group(user_events)

    asyncio.create_task(listener.listen())
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
