from typing import Annotated

from pydantic import BaseModel
from dispytch import Event, Dependency, Router

from dependencies import UserService, get_user_service
from dispytch.kafka import KafkaEventSubscription
from dispytch.middleware import Filter

from custom_middleware import FilterEventType


class User(BaseModel):
    id: str
    email: str
    name: str


class UserCreatedEvent(BaseModel):
    type: str
    user: User
    timestamp: int


user_events = Router()


@user_events.handler(
    KafkaEventSubscription(topic="user_events"),
    middlewares=[FilterEventType("user_registered")]
    # or you can use out-of-the-box Filter middleware instead:
    # Filter(lambda ctx: ctx.event["type"] == "user_registered")
)
async def handle_user_registered(
        event: Event[UserCreatedEvent],
        user_service: Annotated[UserService, Dependency(get_user_service)]
):
    user = event.user
    timestamp = event.timestamp

    print(f"[User Registered] {user.id} - {user.email} at {timestamp}")

    await user_service.do_smth_with_the_user(user)
