import json

from src.deserializer.deserializer import Deserializer
from src.deserializer.exc import FieldMissingError
from src.consumer.models import Payload


class JSONDeserializer(Deserializer):
    def deserialize(self, payload: bytes) -> Payload:
        data = json.loads(payload.decode('utf-8'))

        required_fields = ['type', 'body']
        missing = [field for field in required_fields if data.get(field) is None]
        if missing:
            raise FieldMissingError(*missing)
        return Payload(**data)
