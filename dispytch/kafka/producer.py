from typing import Optional, Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaTimeoutError
from pydantic import BaseModel

from dispytch.emitter.producer import Producer, ProducerTimeout


class KafkaEventConfig(BaseModel):
    partition_key: Optional[Any] = None
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None
    headers: Optional[dict] = None


class KafkaProducer(Producer):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self.producer = producer

    async def send(self, topic: str, payload: bytes, config: BaseModel | None = None) -> None:
        if config is not None and not isinstance(config, KafkaEventConfig):
            raise ValueError(
                f"Expected a KafkaEventConfig when using KafkaProducer got {type(config).__name__}"
            )
        config = config or KafkaEventConfig()

        try:
            await self.producer.send_and_wait(topic=topic,
                                              value=payload,
                                              key=config.partition_key,
                                              partition=config.partition,
                                              timestamp_ms=config.timestamp_ms,
                                              headers=config.headers)
        except KafkaTimeoutError:
            raise ProducerTimeout()
