import msgpack

from dispytch.serialization.deserializer import Deserializer, MessagePayload
from dispytch.serialization.validator import validate_payload


class MessagePackDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> MessagePayload:
        return validate_payload(msgpack.unpackb(payload, raw=False))
