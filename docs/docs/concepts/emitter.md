# 📤 `EventEmitter`

The `EventEmitter` is a core component of Dispytch used to emit (publish) events to an underlying message broker such as
RabbitMQ or Kafka. It abstracts away the details of the producer backend and allows you to send events
with minimal boilerplate.

---

## ✅ Why do I need it?

* **Separation of concerns:** Your app’s business logic shouldn’t wrestle with raw message brokers. `EventEmitter`
  abstracts away the gritty details of RabbitMQ, Kafka, or whatever is under the hood, so you can focus on events—not
  infrastructure.

* **Consistency & safety:** Typed events with `EventBase` ensure your payloads are validated and predictable. No more
  guessing the shape of your data or fumbling with manual serialization.

* **Plug & play with multiple backends:** Whether you’re team Kafka or RabbitMQ (or both), `EventEmitter` lets you
  switch between or postpone backend decisions with less overhead.

* **Testability:** Emitting an event is just calling a method on an object you can mock or swap out—making your code
  easier to test and reason about.

**Bottom line:** `EventEmitter` turns noisy, complex event publishing into a streamlined, reliable, and
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

    * `__topic__`: Target topic for the event.
    * `__event_type__`: Identifier for the type of event.
    * Event payload fields using standard `pydantic` model syntax.

Example:

```python
from dispytch import EventBase


class MyEvent(EventBase):
    __topic__ = "my_topic"
    __event_type__ = "something_happened"

    user_id: str
    value: int
```

---

## ✍️ Example: Setting Up Event Emitter

//// tab | RabbitMQ

```python
import aio_pika
from dispytch import EventEmitter, EventBase
from dispytch.rabbitmq import RabbitMQProducer


class MyEvent(EventBase):
    __topic__ = 'notifications'
    __event_type__ = 'user_registered'

    user_id: str
    email: str


async def main():
    connection = await aio_pika.connect('amqp://guest:guest@localhost:5672')
    channel = await connection.channel()
    exchange = await channel.declare_exchange('notifications', aio_pika.ExchangeType.DIRECT)

    producer = RabbitMQProducer(exchange)
    emitter = EventEmitter(producer)

    await emitter.emit(
        MyEvent(user_id="abc123",
                email="user@example.com")
    )
    print("Event sent!")
```

💡 **Note**: `__topic__` will be used as a routing key when published to exchange

////  
//// tab | Kafka

```python
from aiokafka import AIOKafkaProducer
from dispytch import EventEmitter, EventBase
from dispytch.kafka import KafkaProducer


class MyEvent(EventBase):
    __topic__ = 'user_events'
    __event_type__ = 'user_logged_in'

    user_id: str
    timestamp: str


async def main():
    kafka_raw_producer = AIOKafkaProducer(bootstrap_servers="localhost:19092")
    # The next line is essential. 
    await kafka_raw_producer.start()  # DO NOT FORGET 

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
//// tab | Redis Pub/Sub

```python
# !!! Important: Use the asyncio-compatible Redis client from redis.asyncio
from redis.asyncio import Redis
from dispytch import EventEmitter, EventBase
from dispytch.redis import RedisProducer


class SystemAlert(EventBase):
    __topic__ = "system.alerts"
    __event_type__ = "system_alert"

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
    print(f"Event {event.id} failed to emit!")
```

The callback can be sync or async, and receives the original `EventBase` instance that timed out.

---

## 📌 Notes

* Dispytch automatically **serializes the payload** as JSON by default. To change the default serializer you can
  pass included `MessagePackSerializer` to the EventEmitter or write one on your own
* Event ordering and delivery guarantees — depend on the underlying broker (Kafka/RabbitMQ/Redis), not Dispytch.
