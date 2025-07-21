# 🧠 Dynamic Topics

Dispytch makes event routing flexible and expressive through **dynamic topics**. This allows you to define parameterized
topic structures like `user.{user_id}.notification` and bind them directly to your handler function arguments. Whether
you're building per-tenant pipelines, user-specific notifications, or fine-grained subscriptions, dynamic topics are a
useful tool in Dispytch.

---

## 🔍 What Are Dynamic Topics?

Dynamic topics are topic patterns that contain **segments** identified by curly braces, e.g.:

```python
"user.{user_id}.notification"
```

---

## 🛠️ Use Cases

Some common use cases include:

* **User-specific channels** – `user.{user_id}.notification`
* **Tenant or organization scoping** – `tenant.{tenant_id}.events`
* **Versioned event streams** – `service.{version}.log`

---

## 🧯 Broker Compatibility

Dynamic topics are supported with **all brokers** in Dispytch. However, keep in mind:

* **Redis** (with `psubscribe`) and **AMQP** (with topic exchange routing) are well-suited due to native support for
  wildcards.
* **Kafka** is technically compatible but **not ideal** for dynamic topic models due to:

    * Static topic creation (topics must exist upfront)
    * No wildcard subscription
    * Poor scalability with high topic cardinality

**If you're using Kafka, prefer fewer topics and use event payloads for context and partitions for scalability.**
But if your use case truly needs dynamic topics (e.g., for multi-tenancy separation), you *can* use dynamic topics
carefully.

---

## 🧩 Defining Dynamic Segments with `TopicSegment()`

You can bind dynamic parts of the topic to function parameters using `TopicSegment`.

Here are three ways to use it:

//// tab | **Annotated Parameter (Recommended)**

```python
def handler(user_id: Annotated[int, TopicSegment()]):
    ...
```

////

//// tab | **Class-style Annotation**

```python
def handler(user_id: Annotated[int, TopicSegment]):
    ...
```

Equivalent to the first form, but useful if you forget the parentheses.

////

//// tab | **Default Value**

```python
def handler(user_id: int = TopicSegment()):
    ...
```

You're not allowed to forget the parentheses using this one xD

////

---

## 🪞 Aliases in Dynamic Segments

By default, Dispytch binds the segment name in the topic (e.g., `user_id`) to the **parameter name** in your function.
You can override this using aliases.

### 🏷️ `alias`

Sets the name that Dispytch should expect in the **topic string**.

```python
def handler(uid: Annotated[int, TopicSegment(alias="user_id")]):
    ...
```

In this case, the topic should be:

```
"user.{user_id}.notification"
```

Even though your handler uses `uid`, Dispytch will map `user_id` from the topic to it.

---

### 🧪 `validation_alias`

You can also use `validation_alias`

```python
def handler(uid: int = TopicSegment(validation_alias="user_id")):
    ...
```

---

### 🥷 Both `alias` and `validation_alias`

What if you use both? **`validation_alias` takes precedence** for parsing values from the topic.

```python
def handler(user: int = TopicSegment(alias="ignored", validation_alias="user_id")):
    ...
```

* Topic segment: `user.{user_id}`
* Handler parameter: `user`
* Dispytch looks for `user_id` in the topic (not `ignored`)

---

## ✍️ Example: User-Specific Notifications with Redis

```python
from typing import Annotated
from dispytch import Event, TopicSegment


@listener.handler(topic="user.{user_id}.notification", event="user_notification")
async def handle_notification(event: Event, user_id: Annotated[int, TopicSegment()]):
    print(f"🔔 Notification for user {user_id}: {event.body}")
```

**Given Topic**: `"user.42.notification"`

Dispytch will extract `user_id=42` and pass it to the handler.

---

## ✍️ Example: Using Aliases

```python
@listener.handler(topic="user.{uid}.notification", event="user_notification")
async def handler(user_id: Annotated[int, TopicSegment(alias="uid")]):
    print(f"User ID: {user_id}")
```

Here, Dispytch maps `{uid}` in the topic to the `user_id` parameter.

---

## 🚀 Event Definition

On the producer side, this looks like:

```python
from dispytch import EventBase


class UserNotification(EventBase):
    __topic__ = "user.{user_id}.notification"
    __event_type__ = "user_notification"

    user_id: int
    message: str
```

This allows you to emit events with dynamic topics.

---

## 📤 Emitting Dynamic Events

```python
event = UserNotification(user_id=42, message="Hey there!")
await emitter.emit(event)
```

Dispytch will automatically interpolate the topic:

```
"user.42.notification"
```

---

## 🧪 Validating Topic Parameters

Dynamic topic segments in Dispytch aren't just dumb markers. Under the hood, `TopicSegment()` has the properties of
a **Pydantic `Field`**, which means you can apply **validation constraints** directly to values extracted from the
topic.

This is useful when:

* You want to **restrict allowed values** (e.g., whitelisting with `Literal`)
* You want to apply **numeric bounds** or type checks (e.g., `le=100`, `gt=0`)
* You want to **fail early** if a topic segment is invalid

---

### ✍️ Example: Whitelisting with `Literal`

You can define a handler that only accepts certain literal values:

```python
from typing import Annotated, Literal
from dispytch import TopicSegment


def handler(value: Annotated[Literal["test", "example"], TopicSegment()]):
    ...
```

If the incoming topic contains anything else — like `weirdvalue` — **validation fails**.

---

### ✍️ Example: Range Constraints

You can also enforce constraints like `le` (less than or equal):

```python
def handler(value: Annotated[int, TopicSegment(le=125)]):
    ...
```

If the topic resolves to `value=130`, validation fails and Dispytch raises an error before calling the handler.

---

## 🔗 Topic Delimiters in `EventListener`

When using dynamic topics, Dispytch needs a way to **split topic strings** into segments — this is done using the
`topic_delimiter` argument in the `EventListener`.

```python
listener = EventListener(consumer, topic_delimiter='.')
```

This tells Dispytch to treat topic segments as dot-separated:

```
"user.123.notification"  →  ["user", "123", "notification"]
```

The `topic_delimiter` is used **both for matching incoming topics** and **for extracting values** from dynamic segments.

---

### ⚠️ Important Caveat: Avoid Using the Delimiter in Substituted Values

When you emit or receive an event with a dynamic topic, **substituted values must not contain the delimiter**.
For example:

```python
"user.{value}.notification"
```

With `topic_delimiter='.'`, using `value=7.45` would result in:

```
"user.7.45.notification"
```

This will break matching — because Dispytch will incorrectly split it into:

```
["user", "7", "45", "notification"]
```

#### ✅ DO:

Use values like `745`, `user_45`, or strings that don’t include the delimiter.

#### ❌ DON'T:

Use values that contain the delimiter, like `7.45` with `'.'` or `"foo/bar"` with `'/'`.

---

### 🔒 Broker-Specific Delimiter Constraints

Some brokers **enforce a specific topic delimiter** that cannot be changed:

* **RabbitMQ**: Uses `.` (dot) as the hard-coded separator for topic exchanges.
* **Kafka**: Does *not* split topics by delimiter; full topic names are atomic.
* **Redis (pubsub)**: Allows `psubscribe` with glob patterns, so any delimiter works, but be consistent.

Make sure to align your `topic_delimiter` choice with your broker's behavior.


