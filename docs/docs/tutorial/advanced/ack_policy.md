# ✉️ Acknowledgment Policies

In message broker systems (like Kafka or RabbitMQ), acknowledging (or "acking") a message tells the broker: *"I have
successfully received and handled this event; you do not need to send it to me again."*

Dispytch provides a flexible `AckPolicy` system that allows you to dictate exactly *when* this acknowledgment happens
relative to the execution of your event handlers and middleware pipeline.

---

## ⚙️ How Acknowledgment Policies Work

Under the hood, an `AckPolicy` is a class that implements an `execute` method. When an event is ready to be processed,
the dispatcher passes two callable functions into this policy's `execute` method:

1. **`process_tasks`**: A function that runs the event through your middleware pipeline and executes your registered
   handlers.
2. **`ack_message`**: A function that signals the underlying consumer to actually acknowledge the message to the broker.

By authoring or configuring a policy, you control the order in which these two functions are called.

You can configure acknowledgment policies at two levels:

* **Globally**: By passing a `default_ack_policy` when initializing your `EventDispatcher`. If omitted, it defaults to
  `AckAfterProcessing`.
* **Per-Subscription**: By explicitly calling `dispatcher.set_ack_policy(subscription, policy)` to override the behavior
  for specific routes.

---

## ✅ The Dispytch Way: AckAfterProcessing (Default)

The `AckAfterProcessing` policy is the default, and it represents the strongly preferred way to handle events in
Dispytch.

It fully awaits the `process_tasks()` execution, and only when your handlers and middlewares have finished running does
it call `ack_message()`.

**Why this is the standard:**
This guarantees "at-least-once" delivery. If your application crashes, the database goes down, or an exception is raised
before the handler completes, the message is never acknowledged. The broker will safely redeliver it later. You should
rely on other middlewares (like `Retry` and `ExceptionInterceptor`) to gracefully handle failures *before* the message
is finally acknowledged.

---

## ⚠️ Discouraged: AckBeforeProcessing

Dispytch also includes an `AckBeforeProcessing` policy for flexibility. As the name suggests, it awaits `ack_message()`
to instantly acknowledge the event to the broker, and *then* it awaits `process_tasks()` to execute your handlers.

**This approach is highly discouraged for two critical reasons:**

1. **Data Loss:** If your application crashes or the handler raises an unhandled exception while processing the event,
   the event is permanently lost because the broker has already been told it was handled successfully.
2. **The Unbounded Concurrency Trap:** As detailed in the [Async Processing](../async_processing/async_processing.md),
   limiting concurrency at the consumer level relies on the consumer tracking "in-flight" messages. If you acknowledge a
   message *before* processing completes, the underlying consumer immediately considers the message "done" and fetches
   more. Because the consumer has no visibility into the actual number of in-flight handler tasks, this completely
   breaks native backpressure. This can easily lead to memory exhaustion (OOM errors) and system overloads.

---

## 🏋️ Handling Heavy Workloads

A common temptation for using `AckBeforeProcessing` is to quickly acknowledge a message so the consumer isn't blocked by
a handler that takes several minutes to run (e.g., generating a massive PDF report or processing video).

Instead of early acknowledgment, **heavy processing should be offloaded to dedicated background workers.**

If an event triggers a long-running job:

1. Use the Dispytch handler (with `AckAfterProcessing`) simply to accept the event and push a job payload into a
   dedicated task queue (like Celery, RQ, or another external worker service).
2. Once the job is safely written to the task queue, the Dispytch handler successfully returns.
3. Dispytch then acknowledges the event safely.

This keeps your event processing fast, preserves consumer-level backpressure, and guarantees no events are lost in
transit.

--- 

## 📝 Configuring Acknowledgment Policies

You can configure acknowledgment policies in Dispytch at two different levels: globally for the entire application, or
explicitly overridden for specific event routes.

**Global Configuration**
When you instantiate your `EventDispatcher`, you can pass a `default_ack_policy` parameter. If you do not provide one,
Dispytch automatically defaults to the safe `AckAfterProcessing` policy.

**Per-Subscription Override**
If you have a specific route that requires a different approach—such as a route that strictly offloads its payload to a
background worker and can be acknowledged early—you can explicitly override the global default using the
`set_ack_policy` method on the dispatcher.

```python
from dispytch import EventDispatcher
from dispytch.dispatcher.ack_policy import AckAfterProcessing, AckBeforeProcessing

# 1. Global Configuration
# Setting the default policy for ALL events (this is the default behavior even if omitted)
dispatcher = EventDispatcher(
    consumer=my_consumer,
    default_ack_policy=AckAfterProcessing()
)

# 2. Per-Subscription Override
# Overriding the default to acknowledge early for a specific route
dispatcher.set_ack_policy(
    heavy_video_processing_subscription,
    AckBeforeProcessing()
)

# Register handlers as normal...
# @dispatcher.handler(heavy_video_processing_subscription)
# async def offload_to_worker(event): ...

```
