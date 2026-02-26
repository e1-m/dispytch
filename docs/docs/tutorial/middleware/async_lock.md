# 🔒 AsyncLock Middleware

When your application processes events concurrently, you unlock massive throughput, but you also invite a classic
computer science problem: **race conditions**.

If two events attempting to perform non-atomic operations on the same state concurrently, your async handlers
might read stale data and overwrite each other's changes.

The `AsyncLock` middleware solves this elegantly. It allows you to synchronize the execution of specific events without
sacrificing the overall concurrency of your entire application.

---

## 🔑 Targeted Locking with Key Extractors

To maintain high throughput, you usually do not want to lock your entire handler; you only want to lock events that
affect the *same* resource. `AsyncLock` achieves this using a `key_extractor`.

A `key_extractor` is a simple callable (like a lambda or function) that inspects the `EventHandlerContext` and returns a
unique, hashable value (like a User ID or an Order ID).

Under the hood, Dispytch creates a dedicated `asyncio.Semaphore` for each unique key it encounters. If two events yield
the same key, they are forced to process sequentially. If they yield different keys, they process concurrently without
blocking each other.

```python
from dispytch.middleware import AsyncLock
from dispytch import Router


# Extract the user ID from the event payload
def extract_user_id(ctx):
    return ctx.event.get("user_id")


my_router = Router(middlewares=[AsyncLock(key_extractor=extract_user_id)])


@my_router.handler(my_subscription)
async def update_user_balance(event: dict):
    # Safe! Events for User A will process one at a time.
    # Meanwhile, events for User B will process concurrently alongside User A.
    pass

```

---

## 🚦 Adjusting the Concurrency Limit

By default, the `AsyncLock` allows exactly `1` event per key to process at a time. However, there are scenarios where
you might want to allow a strictly limited number of concurrent executions for the same resource.

You can control this using the `concurrency_limit` parameter. If you set `concurrency_limit=3`, up to three events
sharing
the same key can process simultaneously before a fourth event with that key is forced to wait in line.

```python
# Allow up to 3 simultaneous connections per tenant ID
tenant_lock = AsyncLock(
    key_extractor=lambda ctx: ctx.event.get("tenant_id"),
    concurrency_limit=3
)

```

---

## 🌍 Global Handler Locking

If you omit the `key_extractor` entirely, the middleware automatically applies to every event.

This turns the middleware into a global bottleneck for whatever scope it is applied to. If you apply it to a specific
handler, all events hitting that handler will be forced to process sequentially, one by one, regardless of their
payload.

```python
# No key extractor provided: acts as a strict global lock for this route
fragile_api_lock = AsyncLock(concurrency_limit=1)


@router.handler(legacy_subscription, middlewares=[fragile_api_lock])
async def sync_with_legacy_system(event: dict):
    # Only ONE event will ever execute this code block at a time
    pass

```

