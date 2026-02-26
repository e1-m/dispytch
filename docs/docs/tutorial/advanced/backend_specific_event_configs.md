# ⚙️ Backend-Specific Event Settings

Events often need fine-grained control over how they’re published—things like partitioning, headers, priorities,
timestamps, etc. Dispytch supports this via the optional `__backend_config__` attribute on any `EventBase` object.

This lets you define backend-specific settings inside your event instance in a clean way.

---

## 🧩 What Is `__backend_config__`?

`__backend_config__` is an optional field on `EventBase` instance that lets you pass custom options to your producer. Each backend (Kafka,
RabbitMQ, Redis, etc.) defines its own config schema.

### 🔎 Example

```python
from datetime import datetime
from dispytch import EventBase, EventEmitter
from dispytch.kafka import KafkaEventConfig, KafkaEventRoute


class UserCreated(EventBase):
    __route__ = KafkaEventRoute(
        topic="user_events"
    )
    __backend_config__ = KafkaEventConfig(
        partition_key="{username}",
    )

    username: str
    timestamp: int


async def example_emit(emitter: EventEmitter, username: str):
    event = UserCreated(
        username=username,
        timestamp=int(datetime.now().timestamp()),
    )
    await emitter.emit(event)
```

---

## 🪵 KafkaEventConfig

Use this config to control how events are sent to Kafka.

```python
class KafkaEventConfig(BackendConfig):
    partition_key: Optional[Any] = None
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None
    headers: Optional[dict] = None
```

---

## 🐇 RabbitMQEventConfig

RabbitMQ gives you full control over message delivery via its rich AMQP options.

```python
class RabbitMQEventConfig(BackendConfig):
    delivery_mode: int | None = None
    priority: int | None = None
    expiration: int | datetime | float | timedelta | None = None
    headers: dict | None = None
    content_type: str | None = None
    ...
```

Using this config, you can set AMQP-specific things

---

## 🔨 Implementing Custom Configs

If you're writing a custom producer (see [Writing Custom Producers & Consumers](./own_consumers_and_producers.md)), you can define
your own config schema:

```python
class MyCustomConfig(BackendConfig):
    foo: str
    retries: int = 3
```

Then inspect and apply it inside your `send()` method:

```python
if isinstance(config, MyCustomConfig):
    do_something_with(config.foo)
```
