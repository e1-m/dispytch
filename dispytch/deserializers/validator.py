from dispytch.consumers.deserializer import Payload
from dispytch.deserializers.exc import FieldMissingError


def validate_payload(payload: dict) -> Payload:
    required_fields = ['type', 'body', 'id']
    missing = [field for field in required_fields if payload.get(field) is None]
    if missing:
        raise FieldMissingError(*missing)
    return Payload(**payload)
