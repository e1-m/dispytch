import msgpack

from dispytch.serialization.deserializer import Deserializer


class MessagePackDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> dict:
        return msgpack.unpackb(payload, raw=False)
