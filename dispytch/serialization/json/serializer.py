import json

from dispytch.serialization.serializer import Serializer


class JSONSerializer(Serializer):
    def __init__(self, encoding='utf-8') -> None:
        self.encoding = encoding

    def serialize(self, payload: dict) -> bytes:
        return json.dumps(payload).encode(self.encoding)
