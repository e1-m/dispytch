import asyncio
import logging
from contextlib import asynccontextmanager

from dispytch import EventListener
from dispytch.rabbitmq import RabbitMQConsumer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from user_service.config import settings
from user_service.handlers import post_events
from user_service.rabbitmq_setup import init_rabbit_mq
from user_service.router import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq = await init_rabbit_mq()

    app.state.rabbitmq = rabbitmq

    listener = EventListener(
        RabbitMQConsumer(
            rabbitmq.post_queue,
        )
    )

    listener.add_handler_group(post_events)

    asyncio.create_task(listener.listen())

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
