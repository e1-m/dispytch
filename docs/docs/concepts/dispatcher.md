from dispytch import EventSubscription

# 📥 `EventDispatcher`

`EventDispatcher` is Dispytch’s high-level abstraction for consuming events from a message broker
and dispatching them to appropriate handler functions where your domain logic lives — clean,
decoupled, and dependency-injected.

---

## ✅ Why do I need it?

* **Decoupled event handling:** `EventDispatcher` connects your logic to the outside world without mixing transport
  concerns into your business code. It listens, routes, and invokes handlers—you just write the logic.

* **Event validation:** With `Event[...]` and Pydantic models, your handlers receive structured,
  validated data. No manual parsing, no ambiguous payloads.

* **Built-in dependency injection:** Handlers don’t need to do everything. With first-class support for DI, you can
  split logic into small, testable, reusable functions that plug into the handler automatically.

* **Async execution:** Handlers fully support async execution. Whether you're processing 5 events or 5,000,
  `EventDispatcher`
  doesn’t block on I/O.

* **Flexible retry logic:** Failures happen. With per-handler retry middleware, you decide what’s worth retrying and how
  persistent to be—without bloating your handler code.

* **Organized routing:** With `Router`, you can group related handlers by concern, making
  codebases more maintainable and modular.

* **Backend flexible:** Support for Kafka, RabbitMQ, and Redis PubSub is built-in.
  With clearly defined boundaries for custom transport, you can write your own consumer to fit your specific
  infrastructure needs.

**Bottom line:** `EventDispatcher` gives you a clean, scalable, and testable way to react to events across your system.
Without it, you're hand-wiring consumers, parsing raw payloads, and stuffing all your logic into bloated callback
functions.

---

## 🧱 Basic Structure

```python
dispatcher = EventDispatcher(consumer)


@dispatcher.handler(EventSubscription(...))
async def handle_event(event: Event[T]):
    ...
```

Where:

* `consumer` is an instance of a compatible consumer (e.g. `KafkaConsumer`, `RabbitMQConsumer` or your own)
* `T` is your `pydantic` model for the event body.
* Decorated handler is auto-wired to the event subscription.

---

## ✍️ Example: Setting Up Event Listener

//// tab | RabbitMQ

```python
import aio_pika
from typing import Annotated
from pydantic import BaseModel

from dispytch import EventDispatcher, Event, Dependency
from dispytch.rabbitmq import RabbitMQConsumer, RabbitMQEventSubscription


class MyEventBody(BaseModel):
    user_id: str


async def get_user(event: Event[MyEventBody]):
    yield event.user_id


async def main():
    connection = await aio_pika.connect("amqp://guest:guest@localhost:5672")
    channel = await connection.channel()
    queue = await channel.declare_queue("user.events.my-service")
    exchange = await channel.declare_exchange("user.events", aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange, routing_key="user.registered")

    consumer = RabbitMQConsumer(queue)
    await consumer.start()
    dispatcher = EventDispatcher(consumer)

    @dispatcher.handler(RabbitMQEventSubscription(queue="*", routing_key="user.registered"))
    async def handle_user_reg(
            user_id: Annotated[str, Dependency(get_user)]
    ):
        print(f"Received registration for user {user_id}")

    await dispatcher.start()
```

////
//// tab | Kafka

```python
from aiokafka import AIOKafkaConsumer
from typing import Annotated
from pydantic import BaseModel

from dispytch import EventDispatcher, Event, Dependency
from dispytch.kafka import KafkaConsumer, KafkaEventSubscription
from dispytch.middleware import Filter


class MyEventBody(BaseModel):
    type: str
    action: str
    value: int


async def parse_value(event: Event[MyEventBody]):
    yield event.value


async def main():
    raw_consumer = AIOKafkaConsumer(
        "user_events",
        bootstrap_servers="localhost:19092",
        enable_auto_commit=False,
        group_id="listener_group"
    )
    consumer = KafkaConsumer(raw_consumer)
    await consumer.start()  # REMEMBER TO START YOUR CONSUMER
    dispatcher = EventDispatcher(consumer)

    @dispatcher.handler(
        KafkaEventSubscription(topic="user_events"),
        middlewares=[Filter(lambda ctx: ctx.event["type"] == "user_logged_in")]
    )
    async def handle_login(
            value: Annotated[int, Dependency(parse_value)]
    ):
        print(f"Login action with value: {value}")

    await dispatcher.start()()
```

⚠️ **Important**:

When using Kafka with EventListener, you must manually start the underlying KafkaConsumer.

```python
await consumer.start()
```

////

//// tab | Redis Pub/Sub

```python
# !!! Important: Use the asyncio-compatible Redis client from redis.asyncio
from redis.asyncio import Redis
from pydantic import BaseModel

from dispytch import EventDispatcher, Event
from dispytch.redis import RedisConsumer, RedisEventSubscription


class SystemAlert(BaseModel):
    level: str
    message: str


async def main():
    redis = Redis()
    pubsub = redis.pubsub()

    await pubsub.subscribe("system.alerts")

    consumer = RedisConsumer(pubsub)
    dispatcher = EventDispatcher(consumer)

    @dispatcher.handler(RedisEventSubscription(channel="system.alerts"))
    async def handle_alert(event: Event[SystemAlert]):
        print(f"🚨 [{event.level.upper()}] {event.message}")

    print("🛡️ Listening for system alerts...")
    await dispatcher.start()

```

⚠️ **Important**:

When using RedisConsumer with EventListener,
you should pass the asyncio-compatible Redis client (from redis.asyncio) to the consumer.

////

---

### ⚠️ Notes

* Handlers receive the `Event[T]` param as your Pydantic model
* The event payload must match the Pydantic schema — or decoding will fail.
* Event handling is **async**, and multiple handlers can run concurrently
  if you need to limit concurrency (for example, to avoid race conditions) use AsyncLock middleware

---

## 🧩 `Router`

`Router` allows you to organize and register handlers **modularly**, useful for grouping handlers by concern

### ✅ Use Cases

* Defining a group of related handlers
* Splitting handlers into modules
* Avoiding repetition of middlewares in every decorator

---

### 🔧 Setup

```python
from dispytch import Router
from dispytch.middleware import Retry, ExponentialBackoffWithFullJitter

router = Router(
  middlewares=[Retry(ExponentialBackoffWithFullJitter(retries=5, retry_on=[RetriableError], base_delay_sec=1.25))]
)


@router.handler(EventSubscription(...))
async def handle_user_created(event: Event[...]):
    ...


@router.handler(EventSubscription(...))
async def handle_user_deleted(event: Event[...]):
    ...
```

You can register this `Router` with an `EventDispatcher`:

```python
dispatcher.add_router(router)
```

Behind the scenes, Dispytch will collect all handlers in the group and attach them to the dispatcher.
