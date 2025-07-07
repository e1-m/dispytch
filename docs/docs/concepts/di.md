# 🧪 Dependency Injection (DI)

Dispytch supports a FastAPI-style Dependency Injection system to cleanly manage your handler dependencies—keeping your
logic modular, testable, and DRY.

---

## 💡 Why Use DI?

♻️ Decoupling – Separate business logic from infrastructure concerns

✅ Testability – Easily mock or override dependencies in tests

🔄 Reusability – Centralize shared resources and logic

---

## How It Works

Handlers declare dependencies using Python’s type annotations combined with Dispytch’s `Dependency` wrapper and `Event`
generic class.

Example:

```python
class EventBody(BaseModel):
    value: int
    name: str


async def get_service() -> Service:
    service = Service()
    yield service
    await service.cleanup()


@handler_group.handler(topic="test_events", event="event_type")
async def handle_event(
        # Validates the event payload using EventBody model
        event: Event[EventBody],

        # Injects the result of get_service(); supports automatic cleanup when using context managers
        service: Annotated[Service, Dependency(get_service)]
):
    print(f"Name = {event.body.name} | Value = {event.body.value}")
    await service.do_smth(event.body.value)
```

At runtime, Dispytch:

1. Parses the handler signature.

2. Resolves dependencies using the provided factory functions (sync or async).

3. Injects results directly into the handler.

4. Handles cleanup automatically for context-managed dependencies.

---

## 🧩 Nested Dependencies

Dispytch supports dependency chains—where one dependency depends on another. Each layer is resolved automatically, with
full lifecycle management.

### ✍️ Example

```python
class Config(BaseModel):
    threshold: int = 5


async def get_config() -> Config:
    return Config()


async def get_service(config: Annotated[Config, Dependency(get_config)]):
    service = Service(config.threshold)
    yield service
    await service.cleanup()


@handler_group.handler(topic="nested", event="example")
async def handle_nested(
        event: Event[Any],
        service: Annotated[Service, Dependency(get_service)]
):
    await service.do_smth()
```

### 🔍 What's happening

* `get_service` declares a dependency on `get_config`
* Dispytch resolves `get_config`, then passes the result to `get_service`
* The final resolved `Service` is injected into the handler

---

## 🌐 Context-Aware Dependencies

Dependency functions can receive contextual information about the current event—such as its topic, type, or payload—by
accepting a typed `Event[T]` as an argument.

This enables runtime-aware logic, such as per-event logging, dynamic configuration, or tenant resolution.

---

### ✍️ Example

```python
class Payload(BaseModel):
    user_id: str
    action: str


async def get_logger(event: Event[Payload]) -> Logger:
    # Logger initialized with event metadata
    return Logger(context={
        "topic": event.__topic__,
        "type": event.__event_type__,
        "user_id": event.body.user_id
    })


@handler_group.handler(topic="loggable", event="ctx_aware")
async def handle_event_with_logger(
        event: Event[Payload],
        logger: Annotated[Logger, Dependency(get_logger)]
):
    logger.info(f"User {event.body.user_id} performed action: {event.body.action}")
```

---

### 🧰 Common Use Cases

* 📋 Structured logging – Include event context in every log entry

* 🏢 Per-tenant or per-topic logic – Apply tenant-specific rules or routing

* ⚙️ Dynamic configuration – Adjust behavior based on event payload or headers

## 🔁 Alternative Syntax

As an alternative for the `Annotated[T, Dependency(...)]` style, Dispytch lets you inject dependencies by assigning a
`Dependency` instance directly as a default value for a handler parameter. Functionally the same—just a different
flavor.

> 📋 Note: This injection method **does not work** for the `Event` parameter. You must use explicit type hints for
`Event` to enable proper injection.

### ✍️ Example

```python
async def get_service() -> Service:
    return Service()


@handler_group.handler(topic="alt_usage", event="example")
async def handler_two(
        event: Event,
        service=Dependency(get_service)  # Injected via default argument
):
    await service.do_smth()
```
