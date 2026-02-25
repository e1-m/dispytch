from dispytch import EventSubscription

# 🧪 Dependency Injection (DI)

Dispytch supports a FastAPI-style Dependency Injection system to cleanly manage your handler dependencies—keeping your
logic modular, testable, and DRY.

---

## 💡 Why Use DI?

♻️ Decoupling – Separate business logic from infrastructure concerns

✅ Testability – Mock dependencies in tests

🔄 Reusability – Centralize shared resources and logic

---

## How It Works

Handlers declare dependencies using Python’s type annotations combined with Dispytch’s `Dependency` wrapper.

Example:

```python
class EventBody(BaseModel):
    value: int
    name: str


async def get_service() -> Service:
    service = Service()
    yield service
    await service.cleanup()


@router.handler(EventSubscription(topic="test_events"))
async def handle_event(
        # Validates the event payload using EventBody model
        event: Event[EventBody],

        # Injects the result of get_service(); supports automatic cleanup when using context managers
        service: Annotated[Service, Dependency(get_service)]
):
    print(f"Name = {event.name} | Value = {event.value}")
    await service.do_smth(event.value)
```

At runtime, Dispytch:

1. Resolves dependencies using the provided factory functions (both sync and async).

2. Injects results directly into the handler.

3. Handles cleanup automatically for context-manager-based dependencies.

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


@router.handler(EventSubscription(topic="test_events"))
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

Dependency functions can receive contextual information about the current event
by accepting a typed `Event[T]` as an argument.

---

### ✍️ Example

```python
class Payload(BaseModel):
    user_id: str
    action: str


def get_logger(event: Event[Payload]) -> Logger:
    # Logger initialized with event data
    return Logger(context={
        "user_id": event.user_id
    })


@router.handler(EventSubscription(topic="log_events"))
async def handle_event_with_logger(
        event: Event[Payload],
        logger: Annotated[Logger, Dependency(get_logger)]
):
    logger.info(f"User {event.user_id} performed action: {event.action}")
```

---

## 🔁 Alternative Syntax

As an alternative for the `Annotated[T, Dependency(...)]` style, Dispytch lets you inject dependencies by assigning a
`Dependency` instance directly as a default value for a handler parameter.

> 📋 Note: This injection method **does not work** for the `Event` parameter. You must use explicit type hints for
`Event` to enable proper injection.

### ✍️ Example

```python
def get_service() -> Service:
    return Service()


@router.handler(EventSubscription(topic="alt_usage"))
async def handler_two(
        event: Event,
        service=Dependency(get_service)  # Injected via default argument
):
    await service.do_smth()
```
