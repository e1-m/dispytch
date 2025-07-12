import msgpack

from dispytch.serialization.serializer import Serializer


class MessagePackSerializer(Serializer):
    def serialize(self, payload: dict) -> bytes:
        return msgpack.packb(payload, use_bin_type=True)
