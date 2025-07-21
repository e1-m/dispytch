# ⚙️ Writing Custom Producers & Consumers

Dispytch doesn’t lock you into any specific messaging backend. If you want to connect to something like Redis Streams,
SQS, or whatever queue you want—you can do that by implementing your own `Producer` and `Consumer`.

Here’s how.

---

## 🧪 Custom Producer

To build your own event emitter backend, implement the `Producer` interface.

### ✍️ Interface

```python
class Producer(ABC):
    @abstractmethod
    async def send(self, topic: str, payload: bytes, config: BaseModel | None = None):
        ...
```

### 💡 Notes

* `topic`: where the event goes
* `payload`: bytes containing the event payload
* `config`: optional backend-specific config, usually declared in the event as `__backend_config__`
* If your send logic times out raise `ProducerTimeout`

### ✅ Example (Pseudocode!!!)

```python
from dispytch.emitter.producer import ProducerTimeout, Producer


class RedisProducer(Producer):
    async def send(self, topic: str, payload: bytes, config: BaseModel | None = None):
        result = await redis_client.xadd(topic, payload)
        if not result:
            raise ProducerTimeout("Redis XADD failed")
```

---

## 🧃 Custom Consumer

To receive and handle events from your own backend, implement the `Consumer` interface.

### ✍️ Interface

```python
class Consumer(ABC):
    @abstractmethod
    def listen(self) -> AsyncIterator[Message]:
        ...

    @abstractmethod
    def ack(self, msg: Message):
        ...
```

### 💡 Notes

* `listen()` must yield `Message` objects. This is an **async generator**.

* `ack()` is called when Dispytch successfully processes an event. Use it to mark the event as handled (e.g., ack a
  Kafka offset or delete a message from a queue).

### ✅ Example (Pseudocode!!!)

```python
from dispytch.listener.consumer import Consumer, Message


class RedisConsumer(Consumer):
    async def listen(self) -> AsyncIterator[Message]:
        while True:
            raw = await redis_client.xread(...)
            yield Message(
                topic=raw["stream"],
                payload=raw["payload"]
            )

    def ack(self, msg: Message):
        # Redis streams might not need manual ack, or you could XDEL here
        pass
```

---

## 🛠️ Use Your Custom Classes

Once implemented, you can use your custom producer and consumer classes directly in `EventEmitter` and `EventListener`
