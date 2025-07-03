from aio_pika import Message
from aio_pika.abc import AbstractExchange

from dispytch.emitter.producer import Producer
from dispytch.producers.serializer import Serializer
from dispytch.serializers import JSONSerializer


class RabbitMQProducer(Producer):
    def __init__(self,
                 exchange: AbstractExchange,
                 serializer: Serializer = None) -> None:
        self.exchange = exchange
        self.serializer = serializer or JSONSerializer()

    async def send(self, topic: str, payload: dict) -> None:
        await self.exchange.publish(Message(body=self.serializer.serialize(payload)), routing_key=topic)
