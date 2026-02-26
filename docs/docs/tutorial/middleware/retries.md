# 🔁 Retry Middleware

Handling transient errors—like temporary network drops, database connection issues, or API rate limits—is a critical
part of building resilient event-driven applications. Dispytch provides a built-in `Retry` middleware that catches
exceptions and automatically re-attempts processing the event based on a defined set of rules.

---

### 🚀 How to Use the Retry Middleware

To use the retry functionality, you must instantiate the `Retry` middleware and provide it with a `RetryPolicy`.
Dispytch includes an exponential backoff policy out of the box called `ExponentialBackoffWithFullJitter`.

Here is an example of applying it to a specific handler:

```python
from dispytch.middleware import Retry, ExponentialBackoffWithFullJitter
import requests

# Create a policy that retries up to 3 times, but ONLY for ConnectionError
my_policy = ExponentialBackoffWithFullJitter(
    retries=3,
    retry_on=(ConnectionError,),
    base_delay_sec=2.0,
    max_delay_sec=10.0
)


# Apply the Retry middleware with our policy
@dispatcher.handler(
    user_created_subscription,
    middlewares=[Retry(retry_policy=my_policy)]
)
async def fetch_user_avatar(event: dict):
    # If this raises a ConnectionError, the middleware will catch it and retry
    response = requests.get(event["avatar_url"])
    # ... processing logic

```

---

### ⚠️ The Critical Importance of Order

When defining your middleware lists, **placement of the `Retry` middleware is crucial.**

Under the hood, the `Retry` middleware executes a `while True:` loop wrapped around `await call_next(ctx)`. This means 
**every single middleware placed *after* the `Retry` middleware in the list will be executed again on every single retry
attempt**.

* If you place a logging middleware **before** the `Retry` middleware, it will log the event exactly once when it enters
  the pipeline.
* If you place a logging middleware **after** the `Retry` middleware, it will log the event repeatedly every time a
  retry is triggered.

### 💣 The Danger of Nested Retries

Because middleware pipelines are nested, you must be extremely careful not to apply multiple `Retry` middlewares to the
same execution path.

If you configure a router-level `Retry` middleware with 3 retries, and then accidentally apply a `Retry` middleware on a
specific handler with 3 retries, they will multiply. A failing event won't be retried 6 times—it will be retried **9
times**.
Always ensure your retry logic is applied at the appropriate scope to prevent explosive cascading loops.

---

### 🧠 Retry Policies

A retry policy is the brain behind the middleware.
It dictates exactly *when* an event should be retried and *how long* the system should wait between attempts.

#### The Built-in Policy: ExponentialBackoffWithFullJitter

This built-in policy is highly recommended for distributed systems.
It exponentially increases the delay between attempts (e.g., 1s, 2s, 4s, 8s) up to a maximum limit,
and applies "full jitter" (randomness) to the delay.
Jitter prevents the "thundering herd" problem, where multiple failing instances retry at the exact same millisecond and
overwhelm the system.

You can configure it with the following parameters:

* `retries`: The maximum number of retry attempts.
* `retry_on`: A tuple of specific exception types that should trigger a retry. If omitted, it retries on *all*
  exceptions.
* `base_delay_sec`: The starting baseline delay in seconds.
* `max_delay_sec`: The absolute maximum delay allowed between attempts.

---

### 🛠️ Writing Your Own Retry Policy

If you need a different retry strategy, you can easily write your own policy by inheriting from the abstract
`RetryPolicy` class.

You must implement two abstract methods:

1. `should_retry(attempt: int, error: Exception) -> bool`: Returns `True` if another attempt should be made, or `False`
   to abort and let the exception crash the handler.
2. `get_delay(attempt: int, prev_delay: float) -> float`: Returns the number of seconds to `asyncio.sleep` before making
   the next attempt.

```python
from dispytch.middleware import RetryPolicy


class LinearDelayPolicy(RetryPolicy):
    def __init__(self, retries: int, delay_sec: float):
        self.retries = retries
        self.delay_sec = delay_sec

    def should_retry(self, attempt: int, error: Exception) -> bool:
        # Stop retrying if we've reached the limit
        return attempt < self.retries

    def get_delay(self, attempt: int, prev_delay: float) -> float:
        # Always return the exact same delay, regardless of the attempt number
        return self.delay_sec

```
