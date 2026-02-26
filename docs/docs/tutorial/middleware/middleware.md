# 🧩 Middleware

Middleware in Dispytch is a powerful mechanism that allows you to intercept, inspect, and modify events as they flow
from the consumer to your event handlers.

You can think of middleware as a series of layers wrapped around your core event handlers. When an event arrives, it
passes through each middleware layer before reaching the handler, and the response (or exception) passes back through
those same layers on its way out.

## ❓ Why Use Middleware?

Middleware is ideal for cross-cutting concerns—functionality that you need to apply across many different event handlers
without duplicating code. Common use cases include:

* **Logging and Tracing:** Logging incoming events, execution times, and routing paths.
* **Error Handling:** Catching unexpected exceptions globally and formatting error responses or triggering alerts.
* **Filtering:** Ensuring the event payload meets specific criteria before the handler spends resources processing it.
* **Context Enrichment:** Injecting metadata (like a trace ID or correlation ID) into the context for downstream
  handlers.

---

## 🏗️ The Anatomy of a Middleware

To write your own middleware, you must inherit from the abstract `Middleware` base class and implement the `dispatch`
method.

The `dispatch` method receives two arguments:

1. **`ctx: EventHandlerContext`**: A data class holding the `event` (a dictionary of the payload) and the
   `event_route` (a tuple of strings representing the route).
2. **`call_next: NextCall`**: A callable that triggers the next step in the pipeline. This could be the next middleware
   in the chain, or, if this is the last middleware, the actual event handler.

## 📝 Example: Simple Logging Middleware

Here is how you can write a middleware that logs the route of an incoming event, measures how long it takes to process,
and catches any errors.

```python
import time
import logging
from dispytch import Middleware, EventHandlerContext, NextCall

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
            
            # You should generally return the result of await call_next(ctx) in case upstream callers use it.
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"<-- Error processing {route_str} after {elapsed:.4f}s: {e}")
            raise  # Re-raise the exception so the upstream callers handle it appropriately

```

---

## ⚙️ Middleware Scopes

In Dispytch, middleware is categorized into two primary types: 

 * **Global** (which acts once per event) 
 * **Local** (which acts once per handler call).

### 🌍 Global Middleware (Per Event)

Global middleware applies to *every* event processed by the application, regardless of the route or whether a handler even exists for it.

These middlewares wrap the entire event handling lifecycle.
If a global middleware blocks an event or raises an exception before calling `call_next`,
the dispatcher will never attempt to route the event to your handlers. 
You configure this scope when instantiating your `EventDispatcher`.

```python
from dispytch.dispatcher import EventDispatcher
# ... assuming consumer and other imports are available

# Applying LoggingMiddleware globally to every consumed event
dispatcher = EventDispatcher(
    consumer=my_consumer,
    middlewares=[LoggingMiddleware()]
)

```

### 📍 Local Middleware (Per Handler)

Local middleware is applied *after* the dispatcher has successfully routed an event to one or more matching handlers. \
Every matching handler runs its set of middleware. 

You can apply local middleware in two convenient ways: 
using a **Router** (to group middlewares for multiple handlers) or directly on an **Individual Handler**.
When you use a router, any middleware attached to the router is automatically prepended 
to the middlewares of the handlers registered within it.

```python
from dispytch.dispatcher.router import Router


class AuthenticationMiddleware(Middleware):
    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if "auth_token" not in ctx.event:
            raise ValueError("Unauthorized event")
        return await call_next(ctx)


class FilteringMiddleware(Middleware):
    def __init__(self, event_type: str):
        self.event_type = event_type

    async def dispatch(self, ctx: EventHandlerContext, call_next: NextCall):
        if ctx.event['type'] == self.event_type:
            return None
        return await call_next(ctx)


# 1. Router-Level: Applies to ALL handlers registered to this router
secure_router = Router(middlewares=[AuthenticationMiddleware()])


# 2. Handler-Level: Applies ONLY to this specific handler (combines with Router middlewares)
@secure_router.handler(my_subscription, middlewares=[FilteringMiddleware()])
async def secure_and_filtered_handler(event: dict):
    print("This handler is protected by AuthenticationMiddleware AND ValidationMiddleware!")
    
@secure_router.handler(my_subscription)
async def secure_handler(event: dict):
    print("This handler is protected by AuthenticationMiddleware only!")

```

---


## 🔄 Execution Order

When an event arrives from your consumer, it flows through a composed pipeline. 
The order of execution follows the sequence of your provided lists exactly, operating like an "onion".

The execution follows this specific path:

* **Global Middlewares**: The event enters the global pipeline first. 
  These execute before Dispytch identifies which handlers match the event's route.
* **Local Middlewares**: For each matching handler, its local middleware pipeline executes. 
  This is a combined list where Router middlewares are prepended to the specific Handler's middlewares.

### 📜 The Importance of List Order

1. **Top-Down Execution**: The first middleware in your list is the "outermost" layer. It is the first to execute code before the next layer is called.
2. **Bottom-Up Return**: When the handler finishes, the response (or exception) travels back up through the middlewares in reverse order. This means the first middleware in your list is the last one to execute logic after the handler completes.
