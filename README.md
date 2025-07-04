# ⚡ Dispytch

**Dispytch** is a lightweight, async-first Python framework for event-handling.
It’s designed to streamline the development of clean and testable event-driven services.

## 🚀 Features

* 🧠 **Async-first core** – built for modern Python I/O
* 🔌 **FastAPI-style dependency injection** – clean, decoupled handlers
* 🔁 **Built-in retry logic** – configurable, resilient, no boilerplate 
* 📬 **Backend-flexible** – Kafka and RabbitMQ out-of-the-box
* 🧱 **Composable architecture** – extend, override, or inject anything

---

## 📦 Installation

```bash
pip install dispytch
```

---

## ✨ Simple example

```python
from typing import Annotated

from pydantic import BaseModel

from dispytch import Event, Dependency

from listener import listener
from service import UserService


class User(BaseModel):
    id: str
    email: str
    name: str


class UserCreatedEvent(BaseModel):
    user: User
    timestamp: int


def get_user_service():
    return UserService()


@listener.handler(topic='user_events', event='user_registered', retries=3)
async def handle_user_registered(
        event: Event[UserCreatedEvent],
        user_service: Annotated[UserService, Dependency(get_user_service)]
):
    user = event.body.user
    timestamp = event.body.timestamp

    print(f"[User Registered] {user.id} - {user.email} at {timestamp}")
    await user_service.do_smth_with_the_user(event.body.user)

```

---

## ✅ Why Dispytch?

* 🧼 **Minimal boilerplate** – Just annotate and go
* 🧪 **Testable logic** – Handlers are first-class coroutines
* 🔄 **Flexible backends** – Kafka, RabbitMQ, or bring your own
* 🧩 **Clean separation of concerns** – business logic ≠ plumbing


