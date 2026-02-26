# Middleware

Middleware in Dispytch is a powerful mechanism that allows you to intercept, inspect, and modify events as they flow
from the consumer to your event handlers.

You can think of middleware as a series of layers wrapped around your core event handlers. When an event arrives, it
passes through each middleware layer before reaching the handler, and the response (or exception) passes back through
those same layers on its way out.

### Why Use Middleware?

Middleware is ideal for cross-cutting concerns—functionality that you need to apply across many different event handlers
without duplicating code. Common use cases include:

* **Logging and Tracing:** Logging incoming events, execution times, and routing paths.
* **Error Handling:** Catching unexpected exceptions globally and formatting error responses or triggering alerts.
* **Validation:** Ensuring the event payload meets specific criteria before the handler spends resources processing it.
* **Context Enrichment:** Injecting metadata (like a trace ID or correlation ID) into the context for downstream
  handlers.

---

## The Anatomy of a Middleware

To write your own middleware, you must inherit from the abstract `Middleware` base class and implement the `dispatch`
method.

The `dispatch` method receives two arguments:

1. **`ctx: EventHandlerContext`**: A data class holding the `event` (a dictionary of the payload) and the
   `event_route` (a tuple of strings representing the route).
2. **`call_next: NextCall`**: A callable that triggers the next step in the pipeline. This could be the next middleware
   in the chain, or, if this is the last middleware, the actual event handler.

### Example: A Simple Logging Middleware

Here is how you can write a middleware that logs the route of an incoming event, measures how long it takes to process,
and catches any errors.

```python
import time
import logging
from dispytch.dispatcher.middleware import Middleware, EventHandlerContext, NextCall

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        route_str = "/".join(ctx.event_route)
        logger.info(f"--> Received event for route: {route_str}")

        start_time = time.time()

        try:
            # Pass control to the next middleware or the target handler
            result = await call_next(ctx)

            elapsed = time.time() - start_time
            logger.info(f"<-- Successfully processed {route_str} in {elapsed:.4f}s")

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"<-- Error processing {route_str} after {elapsed:.4f}s: {e}")
            raise  # Re-raise the exception so the dispatcher handles it appropriately

```

---

## Applying Middleware (Scopes)

The `dispytch` framework allows you to apply middleware at three distinct levels: **Global**, **Router**, and **Handler
** (Local).

### 1. Global Middleware (Dispatcher Level)

Global middleware applies to *every* event processed by the application, regardless of which route or handler it is
destined for. You configure this when creating your `EventDispatcher`.

```python
from dispytch.dispatcher import EventDispatcher

# ... assuming consumer and other imports are available

# Applying LoggingMiddleware globally
dispatcher = EventDispatcher(
    consumer=my_consumer,
    middlewares=[LoggingMiddleware()]
)

```

### 2. Router-Level Middleware

If you use a `Router` to group related handlers, you can apply middleware to the entire router. Any middleware provided
to the `Router` is automatically prepended to the handlers registered within that specific router.

```python
from dispytch.dispatcher.router import Router


class AuthenticationMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        # Example: Verify some token in the event payload
        if "auth_token" not in ctx.event:
            raise ValueError("Unauthorized event")
        return await call_next(ctx)


# All routes in this router will require authentication
secure_router = Router(middlewares=[AuthenticationMiddleware()])


@secure_router.handler(my_subscription)
async def secure_handler(event: dict):
    print("This handler is protected by AuthenticationMiddleware!")

```

### 3. Handler-Level Middleware (Local)

For highly specific requirements, you can apply middleware directly to an individual handler. You can do this using the
`middlewares` parameter in the `@handler` decorator on both the `EventDispatcher` and the `Router`.

```python
class ValidationMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if "user_id" not in ctx.event:
            raise ValueError("Missing user_id in payload")
        return await call_next(ctx)


# Applying middleware to a single, specific handler
@dispatcher.handler(user_created_subscription, middlewares=[ValidationMiddleware()])
async def handle_user_creation(event: dict):
    print(f"Processing user: {event['user_id']}")

```

---

## Execution Order

When an event arrives, the middlewares are executed in the following pipeline order:

1. **Global Middlewares** (executed by the `EventDispatcher` around the routing logic).
2. **Router Middlewares + Handler Middlewares** (executed sequentially by the `Handler` wrapper just before Dependency
   Injection and function invocation).

Because `dispytch` composes these layers into a unified pipeline, the outermost middleware (the first one in your global
list) is the first to execute code before `call_next(ctx)`, and the *last* to execute code after `call_next(ctx)`
returns.

