# 📤 `EventEmitter`

The `EventEmitter` is a core component of Dispytch used to publish events to an underlying message broker such as
RabbitMQ, Kafka, or Redis. It abstracts away the details of the producer backend and allows you to send events
with minimal boilerplate.

---

## ✅ Why do I need it?

* **Separation of concerns:** Your app’s business logic shouldn’t wrestle with raw message brokers. `EventEmitter`
  abstracts away the gritty details of RabbitMQ, Kafka, or whatever it is under the hood, so you can focus on events—not
  infrastructure.

* **Consistency & safety:** Typed events with `EventBase` ensure your payloads are validated and predictable.

* **Multiple backends:** Whether you want to use Kafka or RabbitMQ, `EventEmitter` lets you
  switch between or postpone backend decisions with substantially less overhead.

* **Testability:** Emitting an event is just calling a method on an object you can mock or swap out—making your code
  easier to test and reason about.

**Bottom line:** `EventEmitter` turns event publishing into a streamlined, reliable, and
developer-friendly interface. Without it, you’re stuck juggling broker APIs, serialization, and error-prone glue code.

---

## 🧱 Basic Structure

```python
event_emitter = EventEmitter(producer)
await event_emitter.emit(MyEvent(...))
```

`EventEmitter` expects a `Producer` instance (such as `RabbitMQProducer` or `KafkaProducer`) that handles the actual
transport layer.

---

## 🧾 Event Definition

* `MyEvent` inherits from `EventBase` and defines:

    * `__route__`: Target route for the event.
    * `__backend_config__`: Identifier for the type of event.
    * Event payload fields using standard `pydantic` model syntax.

Example:

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


---

## ✍️ Example: Setting Up Event Emitter

//// tab | Kafka

```python
from aiokafka import AIOKafkaProducer
from dispytch import EventEmitter, EventBase
from dispytch.kafka import KafkaProducer, KafkaEventRoute


class MyEvent(EventBase):
    __route__ = KafkaEventRoute(
        topic="user_events",
    )

    user_id: str
    timestamp: str


async def main():
    kafka_raw_producer = AIOKafkaProducer(bootstrap_servers="localhost:19092")
    await kafka_raw_producer.start()  # REMEMBER TO START THE PRODUCER!

    producer = KafkaProducer(kafka_raw_producer)
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="abc123",
                timestamp="2025-07-07T12:00:00Z")
    )
    print("Event emitted!")

```

⚠️ **Important**:

When using Kafka with EventEmitter, you must manually start the underlying AIOKafkaProducer.
Dispytch does not start it for you.

If you forget to call:

```python
await kafka_raw_producer.start()
```

events will not be published, and you won’t get any errors—they’ll just silently vanish into the void.

So don’t skip it. Don’t forget it. Your future self will thank you.

////

//// tab | RabbitMQ

```python
import aio_pika
from dispytch import EventEmitter, EventBase
from dispytch.rabbitmq import RabbitMQProducer, RabbitMQEventRoute


class MyEvent(EventBase):
    __route__ = RabbitMQEventRoute(
        exchange="my.exchange",
        routing_key="my.routing.key",
    )

    user_id: str
    email: str


async def main():
    connection = await aio_pika.connect('amqp://guest:guest@localhost:5672')
    channel = await connection.channel()
    exchange = await channel.declare_exchange('my.exchange', aio_pika.ExchangeType.DIRECT)

    producer = RabbitMQProducer([exchange])
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="abc123",
                email="user@example.com")
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


class SystemAlert(EventBase):
    __route__ = RedisEventRoute(
      channel="system.alerts"
    )

    level: str
    message: str


async def main():
    redis = Redis()

    producer = RedisProducer(redis)
    emitter = EventEmitter(producer)

    await emitter.emit(
        SystemAlert(level="critical",
                    message="CPU temperature high")
    )
    print("Alert sent!")

```

⚠️ **Important**:

When using RedisProducer with EventEmitter,
you should pass the asyncio-compatible Redis client (from redis.asyncio) to the producer.

////

---

## ⏱️ Handling Timeouts with `on_timeout`

By default, if an event fails to emit due to a timeout, Dispytch logs a warning. If you want custom behavior (e.g.,
metrics, retries, alerts), you can register a callback using `on_timeout()`:

```python
@emitter.on_timeout
def handle_timeout(event):
    save_failed_event(event)
```

The callback can be sync or async, and receives the original `EventBase` instance that timed out.

---

## 📦 Serialization

* Dispytch automatically **serializes the payload** as JSON by default. To change the default serializer you can
  pass included `MessagePackSerializer` to the EventEmitter or write one on your own
