from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaTimeoutError
from pydantic import BaseModel

from dispytch.emitter.producer import Producer
from dispytch.producers.serializer import Serializer
from dispytch.serializers import JSONSerializer


class KafkaEventConfig(BaseModel):
    partition_by: Optional[str] = None
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None,
    headers: Optional[dict] = None


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

        partition_key = _extract_partition_key(payload, config.partition_by) if config.partition_by else None

        try:
            await self.producer.send_and_wait(topic=topic,
                                              value=self.serializer.serialize(payload),
                                              key=partition_key,
                                              partition=config.partition,
                                              timestamp_ms=config.timestamp_ms,
                                              headers=config.headers)
        except KafkaTimeoutError:
            ...


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

    if current is None:
        raise ValueError(
            f"Partition key '{partition_key}' is None"
        )

    if not _is_scalar(current):
        raise ValueError(
            f"Partition key '{partition_key}' is not a scalar"
        )

    return current


def _is_scalar(value):
    return isinstance(value, (int, float, complex, bool, str, bytes))
