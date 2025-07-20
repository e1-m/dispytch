import asyncio
from typing import Annotated
from redis.asyncio import Redis
from dispytch import EventListener, TopicSegment, Event
from dispytch.redis import RedisConsumer

from events import UserNotification


async def main():
    redis = Redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("user.*.notification")

    consumer = RedisConsumer(pubsub)

    listener = EventListener(consumer,
                             topic_delimiter='.')

    @listener.handler(topic="user.{user_id}.notification", event="user_notification")
    async def handle_user_event(event: Event[UserNotification],
                                user_id: Annotated[int, TopicSegment()]):
        print(f"📬 Received notification from user {user_id}: {event.body.message}")

    print("👂 Listening for user notifications...")
    await listener.listen()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Shutting down...")
