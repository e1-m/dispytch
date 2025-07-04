import json

from dispytch.consumers.deserializer import Deserializer, Payload
from dispytch.deserializers.validator import validate_payload


class JSONDeserializer(Deserializer):
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def deserialize(self, payload: bytes) -> Payload:
        return validate_payload(json.loads(payload.decode(self.encoding)))
