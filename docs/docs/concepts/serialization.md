# 🧱 Serialization & Deserialization

By default, Dispytch uses JSON for serializing and deserializing events. This keeps things simple and readable—but
you're not stuck with it. If you're sending binary data, need better performance, or just enjoy making things more
complicated than they need to be, you can plug in a custom serializer or deserializer.

## ✍️ Setting a Serializer (Producer Side)

To override the default JSON serializer, pass a serializer instance to your `EventEmitter`:

```python
from dispytch.serialization.msgpack import MessagePackSerializer

emitter = EventEmitter(producer, MessagePackSerializer())
```

If you don’t explicitly pass serializer, `JSONSerializer()` is used under the hood.

## 🧩 Setting a Deserializer (Consumer Side)

Same deal for consumers. You can pick how incoming messages are decoded (should be consistent with sending side, though):

```python
from dispytch.serialization.msgpack import MessagePackDeserializer

listener = EventListener(consumer, MessagePackDeserializer())
```

Again, if you don’t set it, Dispytch will default to `JSONDeserializer()`.

---

## ✨ Writing Your Own

Custom serialization is as simple as implementing a method.

```python
from dispytch.serialization.serializer import Serializer


class MyCoolSerializer(Serializer):
    def serialize(self, payload: dict) -> bytes:
        ...

```

```python
from dispytch.serialization.deserializer import Deserializer, MessagePayload


class MyCoolDeserializer(Deserializer):
    def deserialize(self, data: bytes) -> MessagePayload:
        ...
```
