import msgpack

from dispytch.consumers.deserializer import Deserializer, Payload


class MessagePackDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> Payload:
        return Payload(**msgpack.unpackb(payload, raw=False))
