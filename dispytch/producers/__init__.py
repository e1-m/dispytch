from .serializer import Serializer as Serializer

__all__ = ["KafkaProducer", "RabbitMQProducer", "Serializer"]


def __getattr__(name: str):
    if name == "KafkaProducer":
        try:
            from .kafka import KafkaProducer
            return KafkaProducer
        except ImportError as e:
            raise ImportError(
                "KafkaProducer requires 'aiokafka'. Install dispytch[kafka]"
            ) from e
    elif name == "RabbitMQProducer":
        try:
            from .rabbitmq import RabbitMQProducer
            return RabbitMQProducer
        except ImportError as e:
            raise ImportError(
                "RabbitMQProducer requires 'aio-pika'. Install dispytch[rabbitmq]"
            ) from e
    raise AttributeError(f"module {__name__} has no attribute {name}")
