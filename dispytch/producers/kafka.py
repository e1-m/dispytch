from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from dispytch.emitter.event import KafkaEventConfig
from dispytch.emitter.producer import Producer
from dispytch.producers.serializer import Serializer
from dispytch.serializers import JSONSerializer


class KafkaProducer(Producer):
    def __init__(self, producer: AIOKafkaProducer, serializer: Serializer = None) -> None:
        self.producer = producer
        self.serializer = serializer or JSONSerializer()

    async def send(self, topic: str, payload: dict, config: BaseModel | None = None) -> None:
        if config is not None and not isinstance(config, KafkaEventConfig):
            raise ValueError(
                f"Expected a KafkaEventConfig when using KafkaProducer got {type(config).__name__}"
            )
        config = config or KafkaEventConfig()

        partition_key = _extract_partition_key(payload, config.partition_by)

        await self.producer.send(topic=topic,
                                 value=self.serializer.serialize(payload),
                                 key=partition_key)


def _extract_partition_key(event: dict, partition_key: str):
    parts = partition_key.split('.')
    current = event

    for i, part in enumerate(parts):
        if not isinstance(current, dict):
            raise ValueError(
                f"Expected a nested structure at '{'.'.join(parts[:i])}', got {type(current).__name__}"
            )
        try:
            current = current[part]
        except KeyError:
            raise KeyError(f"Partition key '{partition_key}' not found in event")

    return current
