![Dispytch](docs/docs/assets/images/logo.png)

---

**Dispytch** is an asynchronous Python framework designed to streamline the development of event-driven services.

## 🚀 Features

* 🧠 **Async core** – built for modern Python I/O
* 🔌 **FastAPI-style dependency injection** – clean, decoupled handlers
* 📬 **Pluggable transport layer** – with Kafka, RabbitMQ and Redis PubSub out-of-the-box
* 🧾 **Pydantic v2 validation** – event schemas are validated using pydantic
* 🔁 **Built-in retry logic** – configurable, resilient, no boilerplate
* ✅ **Automatic acknowledgement** – events are acknowledged automatically
* ⚠️ **Error Handling** – handle failures and prevent message loss with DLQ
* ⚖️ **Composable Middleware** – set up logging, metrics, filtering, observability

---

### 💡 See something missing?

Some features aren’t here yet—but with your help, they could be. Contributions welcome via PRs or discussions.

---

## 📦 Installation

Install using [uv](https://github.com/astral-sh/uv) with extras for your preferred backend:

for Kafka support:

```bash
uv add dispytch[kafka]
```

For RabbitMQ support:

```bash
uv add dispytch[rabbitmq]
```

For Redis support:

```bash
uv add dispytch[redis]
```

---

## 📚 Documentation

Full documentation is available:  
👉 [here](https://e1-m.github.io/dispytch/)

---

## ✨ Handler example

```python
from typing import Annotated

from pydantic import BaseModel
from dispytch import Event, Dependency, Router

from dispytch.kafka import KafkaEventSubscription
from dispytch.middleware import Filter


# Service Dependency

class UserService:
    def __init__(self):
        self.users = []

    async def do_smth_with_the_user(self, user):
        print("Doing something with user", user)
        self.users.append(user)


def get_user_service():
    return UserService()


# Event Schemas 

class User(BaseModel):
    id: str
    email: str
    name: str


class UserCreatedEvent(BaseModel):
    type: str
    user: User
    timestamp: int


# Event handler

user_events = Router()


@user_events.handler(
    KafkaEventSubscription(topic="user_events"),
    middlewares=[Filter(lambda ctx: ctx.event["type"] == "user_registered")]
)
async def handle_user_registered(
        event: Event[UserCreatedEvent],
        user_service: Annotated[UserService, Dependency(get_user_service)]
):
    user = event.user
    timestamp = event.timestamp

    print(f"[User Registered] {user.id} - {user.email} at {timestamp}")

    await user_service.do_smth_with_the_user(user)
```

---

## ✨ Emitter example

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from dispytch import EventEmitter, EventBase
from dispytch.kafka import KafkaEventRoute


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


async def example_emit(emitter: EventEmitter):
    await emitter.emit(
        UserRegistered(
            user=User(
                id=str(uuid.uuid4()),
                email="example@mail.com",
                name="John Doe",
            ),
            timestamp=int(datetime.now().timestamp()),
        )
    )
```