import asyncio
from redis.asyncio import Redis  # !!! Important: Use the asyncio-compatible Redis client from redis.asyncio
from dispytch.redis import RedisProducer
from dispytch import EventEmitter
from events import UserNotificationEvent


async def main():
    redis = Redis()

    emitter = EventEmitter(
        RedisProducer(redis)
    )

    for user_id in range(3):
        event = UserNotificationEvent(user_id=user_id,
                                      value=user_id * 10,
                                      message=f"Hello from User {user_id}")
        await emitter.emit(event)
        print(f"✅ Sent: {event.message}")


if __name__ == "__main__":
    asyncio.run(main())
