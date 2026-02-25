import asyncio
import uuid
from datetime import datetime

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from dispytch import EventEmitter, EventBase
from dispytch.kafka import KafkaProducer, KafkaEventRoute


class User(BaseModel):
    id: str
    email: str
    name: str


class UserEvent(EventBase):
    __route__ = KafkaEventRoute(
        topic="user_events"
    )


class UserRegistered(UserEvent):
    type: str = "user_registered"
    user: User
    timestamp: int


async def main():
    kafka_producer = AIOKafkaProducer(bootstrap_servers='localhost:19092')
    await kafka_producer.start()  # IMPORTANT! REMEMBER TO START THE PRODUCER.

    emitter = EventEmitter(KafkaProducer(kafka_producer))

    for i in range(5):
        await emitter.emit(
            UserRegistered(
                user=User(
                    id=str(uuid.uuid4()),
                    email="example@mail.com",
                    name="John Doe",
                ),
                timestamp=int(datetime.timestamp(datetime.now())),
            )
        )
        print(f"event {i} emitted")
        await asyncio.sleep(0.3)

    await kafka_producer.stop()


if __name__ == '__main__':
    asyncio.run(main())
