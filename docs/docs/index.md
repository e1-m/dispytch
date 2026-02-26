#

![Dispytch](assets/images/logo.png)

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

## ✨ Example: Emitting Events

//// tab | Kafka

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

////

//// tab | RabbitMQ

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from dispytch import EventEmitter, EventBase
from dispytch.rabbitmq import RabbitMQEventRoute


class User(BaseModel):
    id: str
    email: str
    name: str


class UserRegistered(EventBase):
    __route__ = RabbitMQEventRoute(
        exchange="user.events",
        routing_key="user.registered"
    )

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

////

//// tab | Redis Pub Sub

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from dispytch import EventEmitter, EventBase
from dispytch.redis import RedisEventRoute


class UserNotification(EventBase):
    __route__ = RedisEventRoute(
        channel="user.{user_id}.notification",
    )

    user_id: int
    message: str
    timestamp: int


async def example_emit(emitter: EventEmitter, user_id: int):
    await emitter.emit(
        UserNotification(
            user_id=user_id,
            message="Hello from Dispytch example",
            timestamp=int(datetime.now().timestamp()),
        )
    )
```

////

## ✨ Example: Handling Events

//// tab | Kafka

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

////

//// tab | RabbitMQ

```python
from typing import Annotated

from pydantic import BaseModel
from dispytch import Event, Dependency, Router

from dispytch.rabbitmq import RabbitMQEventSubscription


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


@user_events.handler(RabbitMQEventSubscription(routing_key="user.registered"))
async def handle_user_registered(
        event: Event[UserCreatedEvent],
        user_service: Annotated[UserService, Dependency(get_user_service)]
):
    user = event.user
    timestamp = event.timestamp

    print(f"[User Registered] {user.id} - {user.email} at {timestamp}")

    await user_service.do_smth_with_the_user(user)

```

////

//// tab | Redis Pub Sub

```python
from typing import Annotated

from pydantic import BaseModel
from dispytch import Event, Dependency, Router, SubscriptionParam

from dispytch.redis import RedisEventSubscription


# Event Schemas 

class UserNotification(BaseModel):
    message: str
    timestamp: int


# Event handler

user_events = Router()


@user_events.handler(RedisEventSubscription(channel="user.{user_id}.notification"))
async def handle_user_notification(
        event: Event[UserNotification],
        user_id: Annotated[int, SubscriptionParam()]
):
    print(f"[User Notification] From: {user_id} - {event.message} at {event.timestamp}")

```

////

