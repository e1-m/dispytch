# 🏗️ Architecture Overview

Dispytch is a lightweight, async-first event-handling framework built with composability and extensibility in mind.
Here’s a breakdown of its core architecture.

---

## 🧩 Core Components

### **🔖 EventBase**

Base class for all events.
Each event is a typed Pydantic model enriched with metadata like `__topic__` and `__event_type__` to control where and
how it gets published and consumed.

```python
class UserRegistered(EventBase):
    __topic__ = "user_events"
    __event_type__ = "user_registered"

    user_id: str
    email: str
```

---

### **📤 EventEmitter**

Handles outbound events.
Wraps a backend-specific producer (Kafka, RabbitMQ, etc.), handling:

* Serialization
* Topic and partition resolution
* Metadata injection

```python
producer = ...  # your backend producer setup
emitter = EventEmitter(producer)


async def emit_user_registered():
    await emitter.emit(UserRegistered(user_id="123", email="user@example.com"))
```

---

### **🧠 HandlerGroup**

A registry for event handlers.
Lets you organize handlers by topic and event type.
Supports dynamic registration and modular grouping.

```python
class UserRegisteredBody(BaseModel):
    user_id: str
    email: str


user_events = HandlerGroup(default_topic="user_events")


@user_events.handler(event="user_registered")
async def handle_user_registered(event: Event[UserRegisteredBody]):
    print(f"User {event.body.user_id} registered with email {event.body.email}")
```

---

### **📥 EventListener**

Handles inbound events.
Consumes events from a backend and dispatches them to relevant handlers—fully async and designed for scale.

```python

consumer = ...  # your backend consumer setup
listener = EventListener(consumer)
listener.add_handler_group(user_events)

if __name__ == "__main__":
    asyncio.run(listener.listen())
```
