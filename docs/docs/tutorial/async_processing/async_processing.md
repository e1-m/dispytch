# ⚡ Async Processing & Concurrency in Dispytch

Dispytch is built from the ground up to be fully asynchronous. When an event arrives, the dispatcher creates an
asynchronous task to handle it, allowing multiple messages to be processed concurrently. If multiple handlers match a
single event route, they are executed concurrently.

While this design provides massive throughput, asynchronous processing introduces complex challenges: **unbounded
concurrency**, **starvation**, **race conditions**, and **out-of-order acknowledgments**. This guide explains how
Dispytch solves these problems and how you should approach concurrency in your applications.

---

## 🌊 The Unbounded Concurrency Trap & Backpressure

If you consume events faster than you can process them, creating a new concurrent task for every single event will
quickly exhaust system resources, leading to Out of Memory (OOM) errors or database connection pool exhaustion. To
prevent this, you need a mechanism to limit concurrency, effectively applying "backpressure."

Dispytch provides two ways to limit concurrency, but they are not created equal.

### 🥇 Best Practice: Consumer-Level Limits

Whenever possible, you should limit concurrency at the consumer level. This provides native backpressure by preventing
the consumer from fetching more messages from the broker until the currently processing ones are finished.

For example, when using Kafka, you can configure a limit on how many messages can be in-flight per partition. If that
limit is reached, the consumer gracefully pauses fetching for that specific partition without blocking the underlying
global event loop.

This approach is the primary way to mitigate the starvation (head-of-line blocking) problem. Because the application is
not constrained by a single global lock, a slow or deadlocked handler on one partition will not prevent Dispytch from
fetching and processing available messages from completely different partitions or topics.

However, relying on this strategy assumes that memory is not a bottleneck for your application. To achieve maximum
throughput while avoiding starvation, these consumer-level limits typically need to be set relatively high.

### ⚠️ When Consumer Limits Fail: The Unbounded Concurrency Risk

Consumer-level limits are not always supported or effective. You must be cautious of two specific scenarios:

1. **Unsupported Brokers:** Some message brokers (like Redis Pub/Sub) do not have built-in concepts of unacknowledged or
   in-flight limits, meaning they will continuously push messages to your application.
2. **Early Acknowledgment Policies:** If you configure an acknowledgment policy that acknowledges an event *before* the
   handler finishes processing it, the underlying consumer immediately considers the message "done". It will then fetch
   more messages. Because the consumer has no visibility into the actual number of actively processing handlers,
   consumer-level backpressure is completely broken, leading straight to unbounded concurrency.

### 🛑 Global Limits (The Fallback) & Starvation Risk

To protect your system when consumer-level limits are not viable (due to the broker type or an early ack policy), you
can enforce a global application-level limit when starting the dispatcher. This restricts the total number of active
handler tasks globally.

**You must use this carefully, as it introduces a high risk of starvation (Head-of-line blocking)**.

* If the global limit is exhausted by tasks that cannot make progress (for example, handlers waiting on a lock or a slow
  network request), the entire application stops fetching new messages.
* Consequently, messages sitting in the underlying consumer that *could* be processed immediately are blocked by the
  stalled tasks.

Use the global limit primarily as a safety net against OOM errors when native backpressure cannot be applied.

---

## 🏎️ Preventing Race Conditions with AsyncLock

When processing messages concurrently, two events affecting the same entity (e.g., two updates to the same user's
balance) might be processed in an overlapping (concurrent) way, leading to a race condition if an external state is
involved

To solve this without sacrificing overall system throughput, Dispytch provides the `AsyncLock` middleware.
(see [Async Lock Middleware](../middleware/async_lock.md))

---

## 🗂️ Safe Async Offset Commits in Kafka

Because Dispytch processes events concurrently, messages from the same Kafka partition will inevitably finish processing
out of order. If a message at offset 10 takes five seconds to process, but the subsequent message at offset 11 takes one
second, offset 11 will finish first.

If Dispytch immediately committed offset 11 to Kafka, and the application crashed before offset 10 finished, offset 10
would be permanently lost (as Kafka assumes all prior offsets are processed).

Dispytch solves this natively using contiguous offset tracking

Dispytch internally tracks the exact sequential order of expected offsets.

* When out-of-order messages finish processing, they are held in a pool.
* The system refuses to advance the "safe to commit" marker until the specific expected sequential message finishes
  processing.
* Once the lagging message finishes, the tracker automatically fast-forwards through all the previously pooled,
  successfully processed messages.

### Batching Commits for Performance

Committing to Kafka for every single message is highly inefficient. Once a safe, contiguous offset is
identified, Dispytch batches these commits in memory.

These batches are only flushed to the Kafka broker based on two configurable triggers:

* **Size:** When the number of pending commits reaches a maximum limit.
* **Time:** When a specific amount of time elapses since the first item was added to the batch.

This ensures your application minimizes network and I/O overhead while guaranteeing data integrity during concurrent
execution.

---

## 🛠️ Configuring Consumer Limits and Offset Batching

When using the `KafkaConsumer`, you can directly configure both the consumer-level backpressure and the offset commit
batching behavior during instantiation.

By tuning these parameters, you control how many messages are held in memory concurrently and how frequently the
consumer communicates with the Kafka broker to save its progress.

```python
from dispytch.kafka import KafkaConsumer
from aiokafka import AIOKafkaConsumer

# Assume you have an underlying aiokafka consumer instance
aio_consumer = AIOKafkaConsumer(...)

# Instantiate the Dispytch KafkaConsumer with custom concurrency and batching limits
my_consumer = KafkaConsumer(
    consumer=aio_consumer,

    # 1. Consumer-Level Backpressure
    # Pauses fetching for a partition if 100 messages from it are currently processing.
    in_flight_msg_limit_per_partition=100,

    # 2. Batching Commits: Size Trigger
    # Flushes offsets to Kafka automatically once 20 contiguous messages have finished.
    batch_size=20,

    # 3. Batching Commits: Time Trigger
    # Flushes offsets to Kafka if 2000ms (2 seconds) pass, even if the batch size isn't reached.
    batch_timeout_ms=2000
)

```

## 🛑 Configuring the Global Concurrency Limit

If you are using a broker that does not support consumer-level backpressure (like Redis Pub/Sub) or if you need a strict
global safety net to prevent Out of Memory (OOM) errors, you can apply a global concurrency limit.

This is applied directly when you start the `EventDispatcher`.

```python
from dispytch.dispatcher import EventDispatcher
import asyncio

dispatcher = EventDispatcher(consumer=my_consumer)


# Register your routes and handlers...
# @dispatcher.handler(...)

async def main():
    # Start the dispatcher with a strict global limit.
    # Dispytch will ensure that no more than 100 handler tasks are actively 
    # executing at the exact same time across the entire application.
    await dispatcher.start(concurrency_limit=100)


if __name__ == "__main__":
    asyncio.run(main())

```

> **Reminder:** Use the global `concurrency_limit` cautiously. If those 100 tasks get stuck waiting on slow external
> APIs, the entire application will stop fetching new messages,
> leading to starvation even if memory allows fetching new messages that can be processed immediately
