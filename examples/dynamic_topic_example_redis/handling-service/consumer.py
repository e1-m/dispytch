import asyncio
from typing import Annotated
from pydantic import BaseModel
from redis.asyncio import Redis  # !!! Important: Use the asyncio-compatible Redis client from redis.asyncio

from dispytch import EventDispatcher, SubscriptionParam, Event
from dispytch.redis import RedisConsumer, RedisEventSubscription


class UserNotification(BaseModel):
    value: int
    message: str


async def main():
    redis = Redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("user.*.notification")

    consumer = RedisConsumer(pubsub)

    listener = EventDispatcher(consumer, route_delimiter='.')

    @listener.handler(RedisEventSubscription(channel="user.{user_id}.notification"))
    async def handle_user_event(event: Event[UserNotification], user_id: Annotated[int, SubscriptionParam()]):
        print(f"📬 Received notification from user {user_id}: {event.message}")

    print("👂 Listening for user notifications...")
    await listener.start()


if __name__ == "__main__":
    asyncio.run(main())
