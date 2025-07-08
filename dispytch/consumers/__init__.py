from .deserializer import Deserializer as Deserializer
from .deserializer import Payload as Payload

__all__ = ["KafkaConsumer", "RabbitMQConsumer", "Deserializer", "Payload"]


def __getattr__(name: str):
    if name == "KafkaConsumer":
        try:
            from .kafka import KafkaConsumer
            return KafkaConsumer
        except ImportError as e:
            raise ImportError(
                "KafkaConsumer requires 'aiokafka'. Install dispytch[kafka]"
            ) from e
    elif name == "RabbitMQConsumer":
        try:
            from .rabbitmq import RabbitMQConsumer
            return RabbitMQConsumer
        except ImportError as e:
            raise ImportError(
                "RabbitMQConsumer requires 'aio-pika'. Install dispytch[rabbitmq]"
            ) from e
    raise AttributeError(f"module {__name__} has no attribute {name}")
