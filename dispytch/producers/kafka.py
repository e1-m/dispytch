from aiokafka import AIOKafkaProducer

from dispytch.emitter.producer import Producer
from dispytch.producers.serializer import Serializer
from dispytch.serializers import JSONSerializer


class KafkaProducer(Producer):
    def __init__(self, producer: AIOKafkaProducer, serializer: Serializer = None) -> None:
        self.producer = producer
        self.serializer = serializer or JSONSerializer()

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def send(self, topic: str, payload: dict) -> None:
        await self.producer.send(topic, value=self.serializer.serialize(payload))
