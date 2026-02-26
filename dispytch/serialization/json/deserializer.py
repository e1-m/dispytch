import json

from dispytch.serialization.deserializer import Deserializer


class JSONDeserializer(Deserializer):
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def deserialize(self, payload: bytes) -> dict:
        return json.loads(payload.decode(self.encoding))
