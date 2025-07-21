# ⚙️ Backend-Specific Event Settings

Events often need fine-grained control over how they’re published—things like partitioning, headers, priorities,
timestamps, etc. Dispytch supports this via the optional `__backend_config__` class attribute on any `EventBase`
subclass.

This lets you define backend-specific settings *inside* your event instance in a clean, declarative way.

---

## 🧩 What Is `__backend_config__`?

`__backend_config__` is an optional `BaseModel` that lets you pass custom options to your producer. Each backend (Kafka,
RabbitMQ, Redis, etc.) can define its own config schema.

### 🔎 Example

```python
class UserCreated(EventBase):
    __topic__ = "user_events"
    __event_type__ = "user_created"

    user: User
    timestamp: int


async def example_emit(emitter: EventEmitter, user: User):
    await emitter.emit(
        UserCreated(
            user=user,
            timestamp=int(datetime.now().timestamp()),
            __backend_config__=KafkaEventConfig(
                partition_key=user.id,
            )
        )

    )
```

---

## 🪵 KafkaEventConfig

Use this config to control how events are sent to Kafka.

```python
class KafkaEventConfig(BaseModel):
    partition_key: Optional[Any] = None
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None
    headers: Optional[dict] = None
```

---

## 🐇 RabbitMQEventConfig

RabbitMQ gives you full control over message delivery via its rich AMQP options.

```python
class RabbitMQEventConfig(BaseModel):
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

If you're writing a custom producer (see [Writing Custom Producers & Consumers](../own_consumers_and_producers/)), you can define
your own config schema:

```python
class MyCustomConfig(BaseModel):
    foo: str
    retries: int = 3
```

Then inspect and apply it inside your `send()` method:

```python
if isinstance(config, MyCustomConfig):
    do_something_with(config.foo)
```
