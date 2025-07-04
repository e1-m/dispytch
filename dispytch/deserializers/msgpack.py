import msgpack

from dispytch.consumers.deserializer import Deserializer, Payload
from dispytch.deserializers.validator import validate_payload


class MessagePackDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> Payload:
        return validate_payload(msgpack.unpackb(payload, raw=False))
