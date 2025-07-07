# 🧱 Serialization & Deserialization

By default, Dispytch uses JSON for serializing and deserializing events. This keeps things simple and readable—but
you're not stuck with it. If you're sending binary data, need better performance, or just enjoy making things more
complicated than they need to be, you can plug in a custom serializer or deserializer.

## ✍️ Setting a Serializer (Producer Side)

To override the default JSON serializer, pass a serializer instance to your `Producer`:

```python
from dispytch.serializers import MessagePackSerializer, JSONSerializer

# Use JSON (default)
producer = KafkaProducer(kafka_producer, JSONSerializer())

# Use MessagePack
producer = KafkaProducer(kafka_producer, MessagePackSerializer())
```

If you don’t explicitly pass one, `JSONSerializer()` is used under the hood.

## 🧩 Setting a Deserializer (Consumer Side)

Same deal for consumers. You can pick how incoming messages are decoded (should be consistent with sending side):

```python
from dispytch.deserializers import MessagePackDeserializer, JSONDeserializer

# Use MessagePack
consumer = KafkaConsumer(kafka_consumer, MessagePackDeserializer())

# Use JSON (default)
consumer = KafkaConsumer(kafka_consumer, JSONDeserializer())
```

Again, if you don’t set it, Dispytch will default to `JSONDeserializer()`.

---

## ✨ Writing Your Own

Custom serialization is as simple as implementing a method.

```python
from dispytch.producers import Serializer


class MyCoolSerializer(Serializer):
    def serialize(self, payload: dict) -> bytes:
        ...

```

```python
from dispytch.consumers import Deserializer, Payload


class MyCoolDeserializer(Deserializer):
    def deserialize(self, data: bytes) -> Payload:
        ...
```
