# 🚀 Quickstart

Get your event-driven flow running with Dispytch in four simple steps.

---

## 1. Define Your Event

Subclass `EventBase` to declare your event’s topic and type metadata, along with its payload:

```python
from dispytch import EventBase


class UserRegistered(EventBase):
    __topic__ = "user_events"
    __event_type__ = "user_registered"

    user_id: str
    email: str
```

---

## 2. Emit Events

Create an `EventEmitter` with your configured backend producer, then emit events asynchronously:

```python
from dispytch.emitter import EventEmitter
from events import UserRegistered

producer = ...  # your backend producer setup
emitter = EventEmitter(producer)

```

```python
async def emit_user_registered(emitter):
    await emitter.emit(UserRegistered(user_id="123", email="user@example.com"))
```

---

## 3. Register Event Handlers

Organize handlers with `HandlerGroup`. Define the event schema (usually a Pydantic model), then decorate your async
handler:

```python
from pydantic import BaseModel
from dispytch import HandlerGroup, Event


class UserRegistered(BaseModel):
    user_id: str
    email: str


user_events = HandlerGroup(default_topic="user_events")


@user_events.handler(event="user_registered")
async def handle_user_registered(event: Event[UserRegistered]):
    print(f"User {event.body.user_id} registered with email {event.body.email}")
```

---

## 4. Start the Listener

Connect your backend consumer to an `EventListener`, register your handler group(s), then listen for incoming events:

```python
import asyncio
from dispytch.listener import EventListener
from handlers import user_events

consumer = ...  # your backend consumer setup
listener = EventListener(consumer)
listener.add_handler_group(user_events)

if __name__ == "__main__":
    asyncio.run(listener.listen())
```

---

## That’s It!

Define events, emit them, handle them asynchronously — all wired up and ready to roll.
