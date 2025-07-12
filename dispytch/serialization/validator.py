from dispytch.serialization.deserializer import MessagePayload
from dispytch.serialization.errors import FieldMissingError


def validate_payload(payload: dict) -> MessagePayload:
    required_fields = ['type', 'body', 'id']
    missing = [field for field in required_fields if payload.get(field) is None]
    if missing:
        raise FieldMissingError(*missing)
    return MessagePayload(**payload)
