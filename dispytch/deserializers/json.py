import json

from dispytch.consumers.deserializer import Deserializer, Payload
from dispytch.deserializers.exc import FieldMissingError


class JSONDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> Payload:
        data = json.loads(payload.decode('utf-8'))

        required_fields = ['type', 'body']
        missing = [field for field in required_fields if data.get(field) is None]
        if missing:
            raise FieldMissingError(*missing)
        return Payload(**data)
