import json

from dispytch.serialization.deserializer import Deserializer, MessagePayload
from dispytch.serialization.validator import validate_payload


class JSONDeserializer(Deserializer):
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def deserialize(self, payload: bytes) -> MessagePayload:
        return validate_payload(json.loads(payload.decode(self.encoding)))
