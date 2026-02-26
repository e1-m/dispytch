from dispytch import EventDispatcher

# 🧠 Dynamic Routes

Dispytch makes event routing flexible and expressive through **dynamic routes**. This allows you to define parameterized
route structures like `user.{user_id}.notification` and bind them directly to your handler function arguments.

---

## 🔍 What Are Dynamic Routes?

Dynamic routes are route patterns that contain **segments** identified by curly braces, e.g.:

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

Dynamic routing is supported with **all brokers** in Dispytch. However, keep in mind:

* **Redis** (with `psubscribe`) and **AMQP** (with topic exchange routing) are well-suited due to native support for
  wildcards.
* **Kafka** is technically compatible but **not ideal** for dynamic routing models due to:

    * Static topic creation (topics must exist upfront)
    * No wildcard subscription
    * Poor scalability with high topic cardinality

**If you're using Kafka, prefer fewer topics and use event payloads for context and partitions for scalability.**
But if your use case truly needs dynamic topics (e.g., for multi-tenancy separation), you *can* use dynamic routing.

Dynamic routing is an application-level feature of Dispytch, independent of your broker’s internal routing.
Dispytch can only process the events your broker is configured to deliver

---

## 🧩 Defining Dynamic Segments with `SubscriptionParam()`

You can bind dynamic parts of the event route to function parameters using `SubscriptionParam`.

Here are three ways to use it:

//// tab | **Annotated Parameter (Recommended)**

```python
def handler(user_id: Annotated[int, SubscriptionParam()]):
    ...
```

////

//// tab | **Class-style Annotation**

```python
def handler(user_id: Annotated[int, SubscriptionParam]):
    ...
```

Equivalent to the first form, but useful if you forget the parentheses.

////

//// tab | **Default Value**

```python
def handler(user_id: int = SubscriptionParam()):
    ...
```

You're not allowed to forget the parentheses using this one xD

////

---

## 🪞 Aliases in Dynamic Segments

By default, Dispytch binds the segment name in the subscription (e.g., `user_id`) to the **parameter name** in your
function.
You can override this using aliases.

### 🏷️ `alias`

Sets the name that Dispytch should expect in the **EventSubscription**.

```python
@router.handler(EventSubscription(channel="user.{user_id}.notification"))
def handler(uid: Annotated[int, SubscriptionParam(alias="user_id")]):
    ...
```

Even though your handler uses `uid`, Dispytch will map `user_id` from the subscription pattern to it.

---

### 🧪 `validation_alias`

You can also use `validation_alias`. If you use both `alias` and `validation_alias` then `validation_alias` takes
precedence.

```python
@router.handler(EventSubscription(channel="user.{user_id}.notification"))
def handler(uid: int = SubscriptionParam(validation_alias="user_id")):
    ...
```

---

## ✍️ Example: User-Specific Notifications with Redis

```python
from typing import Annotated
from dispytch import Event, SubscriptionParam, Router
from dispytch.redis import RedisEventSubscription

router = Router()


@router.handler(RedisEventSubscription(channel="user.{user_id}.notification"))
async def handle_notification(event: Event, user_id: Annotated[int, SubscriptionParam()]):
    print(f"🔔 Notification for user {user_id}: {event.body}")
```

**Given Topic**: `"user.42.notification"`

Dispytch will extract `user_id=42` and pass it to the handler.

---

## ✍️ Example: Using Aliases

```python
from typing import Annotated
from dispytch import Event, SubscriptionParam, Router
from dispytch.redis import RedisEventSubscription

router = Router()


@router.handler(RedisEventSubscription(channel="user.{uid}.notification"))
async def handler(user_id: Annotated[int, SubscriptionParam(alias="uid")]):
    print(f"User ID: {user_id}")
```

Here, Dispytch maps `{uid}` in the channel to the `user_id` parameter.

---

## 🚀 Event Definition

On the producer side, this looks like:

```python
from dispytch import EventBase


class UserNotification(EventBase):
    __router__ = EventRoute(
        channel="user.{user_id}.notification"
    )

    user_id: int
    message: str
```

---

## 📤 Emitting Dynamically Routed Events

```python
await emitter.emit(
    UserNotification(user_id=42, message="Hey there!")
)
```

Dispytch will automatically interpolate the route:

```
"user.42.notification"
```

---

## 🧪 Validating Subscription Parameters

Under the hood, `SubscriptionParam` has the properties of a **Pydantic `Field`**, 
which means you can apply **validation constraints** directly to values extracted from the route.

This is useful when:

* You want to **restrict allowed values** (e.g., whitelisting with `Literal`)
* You want to apply **numeric bounds** or type checks (e.g., `le=100`, `gt=0`)
* You want to **fail early** if a route segment is invalid

---

### ✍️ Example: Whitelisting with `Literal`

You can define a handler that only accepts certain literal values:

```python
from typing import Annotated, Literal
from dispytch import SubscriptionParam


def handler(value: Annotated[Literal["test", "example"], SubscriptionParam()]):
    ...
```

If the incoming route contains anything else — like `weirdvalue` — **validation fails**.

---

### ✍️ Example: Range Constraints

You can also enforce constraints like `le` (less than or equal):

```python
def handler(value: Annotated[int, SubscriptionParam(le=125)]):
    ...
```

If the route resolves to `value=130`, validation fails and Dispytch raises an error before calling the handler.

---

## 🔗 Route Delimiter in `EventDispatcher`

When using dynamic routes, Dispytch needs a way to **split subscription patterns** into segments —
this is done using the `route_delimiter` argument in the `EventDispatcher`.

```python
dispatcher = EventDispatcher(consumer, route_delimiter='.')
```

This tells Dispytch to treat route segments as dot-separated:

```
"user.123.notification"  →  ["user", "123", "notification"]
```

---

### ⚠️ Important Caveat: Avoid Using the Delimiter in Substituted Values

When you emit or receive an event with a dynamic route, **substituted values must not contain the delimiter**.
For example:

```python
"user.{value}.notification"
```

With `route_delimiter='.'`, using `value=7.45` would result in:

```
"user.7.45.notification"
```

This will break matching — because Dispytch will incorrectly split it into:

```
["user", "7", "45", "notification"]
```

Avoid using values that contain your delimiter, like `7.45` with `'.'` or `"user_id"` with `'_'`.

---

### 🔒 Broker-Specific Delimiter Constraints

Some brokers **enforce a specific delimiter** for their internal routing that cannot be changed:

* **RabbitMQ**: Uses `.` (dot) as the hard-coded separator for wildcards.
* **Kafka**: Does *not* split topics by delimiter; full topic names are atomic.
* **Redis (PubSub)**: Allows `psubscribe` with glob patterns, so any delimiter works, but be consistent.

Make sure to align your `route_delimiter` choice with your broker's routing behavior.


