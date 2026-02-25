# 🧱 Serialization & Deserialization

By default, Dispytch uses JSON for serializing and deserializing events. This keeps things simple—but
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

Same deal for consumers. You can pick how incoming messages are decoded:

```python
from dispytch.serialization.msgpack import MessagePackDeserializer

listener = EventDispatcher(consumer, MessagePackDeserializer())
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
from dispytch.serialization.deserializer import Deserializer


class MyCoolDeserializer(Deserializer):
    def deserialize(self, data: bytes) -> dict:
        ...
```
