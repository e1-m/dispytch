import msgpack

from dispytch.consumers.deserializer import Deserializer, Payload
from dispytch.deserializers.exc import FieldMissingError


class MessagePackDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> Payload:
        data = msgpack.unpackb(payload, raw=False)

        required_fields = ['type', 'body']
        missing = [field for field in required_fields if data.get(field) is None]
        if missing:
            raise FieldMissingError(*missing)
        return Payload(**data)
