# 🛡️ Exception Interceptor Middleware

When building robust event-driven systems, things inevitably go wrong. Whether it is a malformed payload, a missing
database record, or a downstream service outage, your application needs a way to catch and handle these errors
gracefully.

In Dispytch, the `ExceptionInterceptor` middleware provides an elegant mechanism to catch exceptions raised during the
execution of your event pipeline and route them to specific error-handling functions based on the exception's type.

## ⚠️ Crucial Note on Scope: Use Locally, Not Globally

It is strictly recommended to apply the `ExceptionInterceptor` as **Local Middleware** (on a Router or Handler), and
never as Global Middleware on the Dispatcher.

Here is why: At the global dispatcher level, Dispytch executes all matching handlers concurrently and aggregates their
results using `asyncio.gather(*tasks, return_exceptions=True)`. Because exceptions are caught and returned as a list of
results at the global level, a global `ExceptionInterceptor` will simply receive a list of return values and will not
trigger its `except Exception as err:` block for individual handler failures.

By applying it locally, the interceptor wraps the specific handler's execution directly, successfully catching the
raised exceptions before they are aggregated by the global dispatcher.

---

## 🚀 Basic Usage: Function Handlers

The `ExceptionInterceptor` requires a dictionary mapping exception types to asynchronous handler functions.

When an exception is raised in your handler, the middleware intercepts it. If the exception matches a registered type,
the middleware delegates the execution to your custom handler. If it does not match, it is re-raised.

Here is an example using simple asynchronous functions applied at the Router level:

```python
from dispytch import Router, EventHandlerContext
from dispytch.middleware import ExceptionInterceptor


async def handle_value_error(ctx: EventHandlerContext, err: Exception):
    print(f"Validation failed for route {ctx.event_route}: {err}")
    return "validation_failed_handled"


async def handle_type_error(ctx: EventHandlerContext, err: Exception):
    print(f"Type mismatch: {err}")
    return "type_error_handled"


# Instantiate the middleware with your mappings
error_middleware = ExceptionInterceptor(handlers={
    ValueError: handle_value_error,
    TypeError: handle_type_error
})

# Apply it LOCALLY to a Router or a handler
my_router = Router(middlewares=[error_middleware])


@my_router.handler(my_subscription)
async def process_data(event: dict):
    # If a ValueError is raised here, error_middleware catches it!
    raise ValueError("Bad data")

```

---

## 🧠 Stateful Object Handlers

Sometimes, simple functions are not enough. You might need your error handler to maintain state, such as keeping track
of how many times a specific error has occurred, or holding a reference to an external alerting service.

Because the `ExceptionInterceptor` accepts any `Callable` that returns an `Awaitable`, you can easily pass an instance
of a class that implements the `__call__` dunder method.

```python
class AlertingErrorHandler:
    def __init__(self, alert_service):
        self.alert_service = alert_service
        self.error_count = 0

    async def __call__(self, ctx: EventHandlerContext, err: Exception):
        self.error_count += 1
        print(f"Total critical errors: {self.error_count}")

        # Trigger an external alert using the injected state
        await self.alert_service.send_alert(f"Critical failure: {err}")
        return "alert_sent"


# Instantiate your stateful handler
db_alerter = AlertingErrorHandler(alert_service=my_pagerduty_client)

# Register it with the interceptor
interceptor = ExceptionInterceptor(handlers={
    ConnectionError: db_alerter
})

```

---

## 🧬 Exception Inheritance and Precedence

One of the most useful behaviors of the `ExceptionInterceptor` is how it handles exception hierarchies. It does not
just look for exact class matches; it respects Python's Method Resolution Order (MRO).

This means the middleware evaluates the exception's inheritance tree to find the closest matching handler.

Here is how the order of evaluation works:

* **Subclass Catching**: If you register a handler for `ValueError`, and a custom exception
  `class MyError(ValueError): pass` is raised, the `ValueError` handler will successfully catch it.
* **Precedence (Specificity Wins)**: If you register handlers for both a parent exception and a child exception, the
  middleware will always execute the handler for the most specific (child) exception.

```python
class DatabaseError(Exception):
    pass


class RecordNotFoundError(DatabaseError):
    pass


class ConsistencyError(DatabaseError):
    pass


async def handle_generic_db_error(ctx, err):
    return "generic_db_handler"


async def handle_not_found(ctx, err):
    return "not_found_handler"


# Registering both parent and child
interceptor = ExceptionInterceptor(handlers={
    DatabaseError: handle_generic_db_error,
    RecordNotFoundError: handle_not_found
})

# If RecordNotFoundError is raised, `handle_not_found` is called.
# If ConsistencyError (or another DatabaseError subclass) is raised, `handle_generic_db_error` acts as the fallback.

```

---

## ➕ Alternative Setup: Adding Handlers After Instantiation

You do not have to define all your error handlers upfront in the constructor's dictionary. The middleware exposes an
`add_handler` method, providing an alternative way to register exception handlers during your application's setup phase.

```python
interceptor = ExceptionInterceptor(handlers={})


async def missing_key_handler(ctx, err):
    return "missing_key_handled"


# Add a handler as an alternative to passing it in the constructor
interceptor.add_handler(KeyError, missing_key_handler)

```