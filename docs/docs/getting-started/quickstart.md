# 🚀 Quickstart

Get your event-driven flow running with Dispytch in four simple steps.

---

## 1. Define Your Event

Subclass `EventBase` to declare your event’s route, along with its payload:

//// tab | Kafka

```python
from dispytch import EventBase
from dispytch.kafka import KafkaEventRoute


class MyEvent(EventBase):
    __route__ = KafkaEventRoute(
        topic="my_topic",
    )

    user_id: str
    value: int
```

////  
//// tab | RabbitMQ

```python
from dispytch import EventBase
from dispytch.rabbitmq import RabbitMQEventRoute


class MyEvent(EventBase):
    __route__ = RabbitMQEventRoute(
        exchange="my.exchange",
        routing_key="my.routing.key",
    )

    user_id: str
    value: int
```

////

//// tab | Redis Pub/Sub

```python
from dispytch import EventBase
from dispytch.redis import RedisEventRoute


class MyEvent(EventBase):
    __route__ = RedisEventRoute(
        channel="my.channel",
    )

    user_id: str
    value: int
```

////

## 2. Emit Events

Create an `EventEmitter` with your configured backend producer, then emit events asynchronously:

//// tab | Kafka

```python
from aiokafka import AIOKafkaProducer
from dispytch import EventEmitter, EventBase
from dispytch.kafka import KafkaProducer, KafkaEventRoute


async def main():
    kafka_raw_producer = AIOKafkaProducer(bootstrap_servers="localhost:19092")
    await kafka_raw_producer.start()  # REMEMBER TO START THE PRODUCER!

    producer = KafkaProducer(kafka_raw_producer)
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="user_123", value=123)
    )
    print("Event sent!")

```

////

//// tab | RabbitMQ

```python
import aio_pika
from dispytch import EventEmitter, EventBase
from dispytch.rabbitmq import RabbitMQProducer, RabbitMQEventRoute


async def main():
    connection = await aio_pika.connect('amqp://guest:guest@localhost:5672')
    channel = await connection.channel()
    exchange = await channel.declare_exchange('my.exchange', aio_pika.ExchangeType.DIRECT)

    producer = RabbitMQProducer([exchange])
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="user_123", value=123)
    )
    print("Event sent!")
```

////

//// tab | Redis Pub/Sub

```python
# !!! Important: Use the asyncio-compatible Redis client from redis.asyncio
from redis.asyncio import Redis
from dispytch import EventEmitter, EventBase
from dispytch.redis import RedisProducer, RedisEventRoute


async def main():
    redis = Redis()

    producer = RedisProducer(redis)
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="user_123", value=123)
    )
    print("Event sent!")

```

////

## 3. Register Event Handlers

Organize handlers with `Router`. Define the event schema using Pydantic BaseModel, then decorate your handler function:

//// tab | Kafka

```python
from pydantic import BaseModel
from dispytch import Router, Event
from dispytch.kafka import KafkaEventSubscription


class MyEvent(BaseModel):
    user_id: str
    value: int


my_router = Router()


@my_router.handler(KafkaEventSubscription(topic="my_topic"))
async def handle_user_event(event: Event[MyEvent]):
    print(f"Received user event from user: {event.user_id} with value: {event.value}")
```

////

//// tab | RabbitMQ

```python
from pydantic import BaseModel
from dispytch import Router, Event
from dispytch.rabbitmq import RabbitMQEventSubscription


class MyEvent(BaseModel):
    user_id: str
    value: int


my_router = Router()


@my_router.handler(RabbitMQEventSubscription(routing_key="my.routing.key"))
async def handle_user_event(event: Event[MyEvent]):
    print(f"Received user event from user: {event.user_id} with value: {event.value}")
```

////

//// tab | Redis PubSub

```python
from pydantic import BaseModel
from dispytch import Router, Event
from dispytch.redis import RedisEventSubscription


class MyEvent(BaseModel):
    user_id: str
    value: int


my_router = Router()


@my_router.handler(RedisEventSubscription(channel="my.channel"))
async def handle_user_event(event: Event[MyEvent]):
    print(f"Received user event from user: {event.user_id} with value: {event.value}")
```

////


---

## 4. Start the Dispatcher

Connect your backend consumer to an `EventDispatcher`, register your handler group(s), then listen for incoming events:

//// tab | Kafka

```python
import asyncio
from aiokafka import AIOKafkaConsumer
from dispytch.dispatcher import EventDispatcher
from dispytch.kafka import KafkaConsumer
from routers import my_router


async def main():
    consumer = KafkaConsumer(
        AIOKafkaConsumer(
            "my_topic",
            bootstrap_servers="localhost:9092",
            enable_auto_commit=False,  # must be false, dispytch handles offsets
            group_id='consumer_group_id',
            auto_offset_reset='earliest'
        )
    )
    await consumer.start()

    dispatcher = EventDispatcher(consumer)
    dispatcher.add_router(my_router)
    await dispatcher.start()


if __name__ == "__main__":
    asyncio.run(main())
```

////

//// tab | RabbitMQ

```python
import asyncio
from dispytch.dispatcher import EventDispatcher
from dispytch.rabbitmq import RabbitMQConsumer
from routers import my_router
from queues import queue_one, queue_two


async def main():
    consumer = RabbitMQConsumer(queue_one, queue_two)
    await consumer.start()

    dispatcher = EventDispatcher(consumer)
    dispatcher.add_router(my_router)
    await dispatcher.start()


if __name__ == "__main__":
    asyncio.run(main())
```

////

//// tab | Redis PubSub

```python
import asyncio
from redis.asyncio import Redis
from dispytch.dispatcher import EventDispatcher
from dispytch.redis import RedisConsumer
from routers import my_router


async def main():
    redis = Redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("my.channel")

    consumer = RedisConsumer(pubsub)


    dispatcher = EventDispatcher(consumer)
    dispatcher.add_router(my_router)
    await dispatcher.start()


if __name__ == "__main__":
    asyncio.run(main())
```

////

---

## That’s It!

Define events, emit them, handle them asynchronously — all wired up with di and middleware.
