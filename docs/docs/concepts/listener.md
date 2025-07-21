# 📥 `EventListener`

`EventListener` is Dispytch’s high-level abstraction for consuming events from a message broker (like Kafka or RabbitMQ)
and dispatching them to appropriate async handler functions. It’s where your event-driven logic lives — clean,
decoupled, and dependency-injected.

---

## ✅ Why do I need it?

* **Decoupled event handling:** `EventListener` connects your logic to the outside world without mixing transport
  concerns into your business code. It listens, routes, and invokes handlers—you just write the logic.

* **Strong typing, minimal guesswork:** With `Event[...]` and Pydantic models, your handlers receive structured,
  validated data. No manual parsing, no ambiguous payloads.

* **Built-in dependency injection:** Handlers don’t need to do everything. With first-class support for DI, you can
  split logic into small, testable, reusable functions that plug into the handler automatically.

* **Async-native execution:** Handlers are fully async. Whether you're processing 10 events or 10,000, `EventListener`
  doesn’t block or get in your way.

* **Flexible retry logic:** Failures happen. With per-handler retry controls, you decide what’s worth retrying and how
  persistent to be—without bloating your handler code.

* **Organized and scalable:** With `HandlerGroup`, you can group related handlers by topic or concern, making
  codebases more maintainable and modular.

* **Backend agnostic:** Whether you're consuming from Kafka, RabbitMQ, or anything else behind a compatible consumer,
  the interface stays the same—clean and stable.

**Bottom line:** `EventListener` gives you a clean, scalable, and testable way to react to events across your system.
Without it, you're hand-wiring consumers, parsing raw payloads, and stuffing all your logic into bloated callback
functions.

---

## 🧱 Basic Structure

```python
event_listener = EventListener(consumer)


@event_listener.handler(topic="...", event="...")
async def handle_event(event: Event[T]):
    ...
```

Where:

* `consumer` is an instance of a compatible consumer (e.g. `KafkaConsumer`, `RabbitMQConsumer` or your own)
* `T` is your `pydantic` model for the event body.
* Decorated handler is auto-wired to the event type via `topic` + `event`.

---

## ✍️ Example: Setting Up Event Listener

//// tab | RabbitMQ

```python
import aio_pika
from typing import Annotated
from pydantic import BaseModel

from dispytch import EventListener, Event, Dependency
from dispytch.rabbitmq import RabbitMQConsumer


class MyEventBody(BaseModel):
    user_id: str


async def get_user(event: Event[MyEventBody]):
    yield event.body.user_id


async def main():
    connection = await aio_pika.connect("amqp://guest:guest@localhost:5672")
    channel = await connection.channel()
    queue = await channel.declare_queue("notifications")
    exchange = await channel.declare_exchange("notifications", aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange, routing_key="notifications")

    consumer = RabbitMQConsumer(queue)
    listener = EventListener(consumer)

    @listener.handler(topic="notifications", event="user_registered")
    async def handle_user_reg(
            user_id: Annotated[str, Dependency(get_user)]
    ):
        print(f"Received registration for user {user_id}")

    await listener.listen()
```

////
//// tab | Kafka

```python
from aiokafka import AIOKafkaConsumer
from typing import Annotated
from pydantic import BaseModel

from dispytch import EventListener, Event, Dependency
from dispytch.kafka import KafkaConsumer


class MyEventBody(BaseModel):
    action: str
    value: int


async def parse_value(event: Event[MyEventBody]):
    yield event.body.value


async def main():
    raw_consumer = AIOKafkaConsumer(
        "user_events",
        bootstrap_servers="localhost:19092",
        enable_auto_commit=False,
        group_id="listener_group"
    )
    # the next line is essential
    await raw_consumer.start()  # DO NOT FORGET
    consumer = KafkaConsumer(raw_consumer)
    listener = EventListener(consumer)

    @listener.handler(topic="user_events", event="user_logged_in")
    async def handle_login(
            value: Annotated[int, Dependency(parse_value)]
    ):
        print(f"Login action with value: {value}")

    await listener.listen()
```

⚠️ **Important**:

When using Kafka with EventListener, you must manually start the underlying AIOKafkaConsumer.
Dispytch does not start it for you.

If you forget to call:

```python
await raw_consumer.start()
```

events will not be consumed, and you won’t get any errors—they’ll just silently vanish into the void.

So don’t skip it. Don’t forget it. Your future self will thank you.

////

//// tab | Redis Pub/Sub

```python
# !!! Important: Use the asyncio-compatible Redis client from redis.asyncio
from redis.asyncio import Redis
from pydantic import BaseModel

from dispytch import EventListener, Event
from dispytch.redis import RedisConsumer


class SystemAlert(BaseModel):
    level: str
    message: str


async def main():
    redis = Redis()
    pubsub = redis.pubsub()

    await pubsub.subscribe("system.alerts")

    consumer = RedisConsumer(pubsub)
    listener = EventListener(consumer)

    @listener.handler(topic="system.alerts", event="system_alert")
    async def handle_alert(event: Event[SystemAlert]):
        print(f"🚨 [{event.body.level.upper()}] {event.body.message}")

    print("🛡️ Listening for system alerts...")
    await listener.listen()

```

⚠️ **Important**:

When using RedisConsumer with EventListener,
you should pass the asyncio-compatible Redis client (from redis.asyncio) to the consumer.

////

---

### ⚠️ Notes & Gotchas

* Handlers receive the full `Event[T]` with your typed payload (Pydantic model) under `.body`:
* The event payload must match the Pydantic schema — or decoding will fail.
* The `event` string must match `__event_type__` of the published event.
* Event handling is **fully async**, and multiple handlers can run concurrently.
* You can attach **multiple handlers** to the same topic and event type.

---

## 🔁 Retries

Handlers can be configured to **automatically retry** on failure using `retries`, `retry_on`, and `retry_interval`.

### 🎯 Parameters:

* `retries`: Number of retry attempts (default: `0`)
* `retry_on`: list of exception types to trigger retry. If `None`, all exceptions will trigger retry.
* `retry_interval`: Delay (in seconds) between retries (default: `1.25`)

### ✅ Example:

```python
@listener.handler(
    topic="critical_events",
    event="do_or_die",
    retries=3,
    retry_on=[RuntimeError],
    retry_interval=2.0
)
async def handle_critical(event: Event[MyEventBody]):
    print("Processing...")
    raise RuntimeError("Temporary failure")
```

In this example, the handler will retry up to 3 times **only** if a `RuntimeError` is raised, waiting 2 seconds between
attempts.

💡 *If you don't set `retry_on`, all exceptions will trigger a retry — use with caution.*

---

## 🧩 `HandlerGroup`

`HandlerGroup` allows you to organize and register handlers **modularly**, useful for grouping handlers by topic or
event type.

### ✅ Use Cases

* Defining a group of related handlers
* Splitting handlers into modules
* Avoiding repetition of `topic`/`event` in every decorator

---

### 🔧 Setup

```python
from dispytch import HandlerGroup

group = HandlerGroup(default_topic="my_topic", default_event="default_type")


@group.handler(event="user_created")
async def handle_user_created(event: Event[...]):
    ...


@group.handler(event="user_deleted", retries=2)
async def handle_user_deleted(event: Event[...]):
    ...
```

You can register this `HandlerGroup` with an `EventListener`:

```python
listener.add_handler_group(group)
```

Behind the scenes, Dispytch will collect all handlers in the group and attach them to the listener.

---

### 🎯 Group Config Behavior

* `topic` and `event` in the decorator **override** group defaults.
* If **neither** is set (decorator or default), you get a `TypeError`.
