# 🛑 Filter Middleware

In event-driven architectures, you often consume from a broad stream of events (like a single Kafka topic) but only want
a specific handler to process a subset of those events. The `Filter` middleware allows you to conditionally control
whether an event continues down the pipeline.

---

## 🚀 Using the Built-in Filter Middleware

Dispytch provides a built-in `Filter` middleware out of the box. It accepts a `Callable` (like a lambda function) that
evaluates the `EventHandlerContext` and returns a boolean.

Here is an example of how you might use it to filter events from a Kafka topic, ensuring the handler only executes if
the event is specifically a "user_registered" event:

```python
from dispytch.middleware import Filter


@user_events.handler(
    KafkaEventSubscription(topic="user_events"),
    # The lambda function checks the 'type' field in the event dictionary
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

## 🛠️ Writing Custom Filters for Cleaner Code

While the built-in `Filter` using lambda functions is great for quick, one-off checks, writing
`Filter(lambda ctx: ctx.event["type"] == ...)` on every single route can quickly become repetitive and clutter your
codebase.

When you know the consistent structure of your events—such as having a standard `type` key in the payload—you can easily
implement a custom filter middleware to make your handler declarations much cleaner and declarative.

Instead of wrapping a lambda, you create a new class that inherits directly from `Middleware` and implements the
`dispatch` method.

Here is how you can write a reusable `FilterEventType` middleware:

```python
from dispytch import Middleware, EventHandlerContext, NextCall


class FilterEventType(Middleware):
    def __init__(self, event_type: str):
        self.event_type = event_type

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        # Check if the incoming event matches the required type
        if ctx.event.get('type') == self.event_type:
            # Condition met: proceed to the next layer in the pipeline
            return await call_next(ctx)

        # Condition failed: drop the event silently
        return None

```

Now, you can update your handler decorator to use this custom, highly readable middleware instead:

```python
@user_events.handler(
    KafkaEventSubscription(topic="user_events"),
    # Much cleaner and self-documenting!
    middlewares=[FilterEventType("user_registered")]
)
async def handle_user_registered(
        event: Event[UserCreatedEvent],
        user_service: Annotated[UserService, Dependency(get_user_service)]
):
# ... handler logic

```

