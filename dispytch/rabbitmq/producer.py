from asyncio import TimeoutError
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from aio_pika import Message
from aio_pika.abc import AbstractExchange, DeliveryMode
from pydantic import BaseModel

from dispytch.emitter.producer import Producer, ProducerTimeout, EventRoute


class RabbitMQEventConfig(BaseModel):
    delivery_mode: DeliveryMode | int | None = None
    priority: int | None = None
    expiration: int | datetime | float | timedelta | None = None
    headers: dict[str, bool | bytes | Decimal | list | dict[
        str, Any] | float | int | None | str | datetime] | None = None
    content_type: str | None = None
    content_encoding: str | None = None
    correlation_id: str | None = None
    reply_to: str | None = None
    message_id: str | None = None
    timestamp: int | datetime | float | timedelta | None = None
    type: str | None = None
    user_id: str | None = None
    app_id: str | None = None


class RabbitMQEventRoute(EventRoute):
    def __init__(self, exchange: str, routing_key: str):
        self.exchange = exchange
        self.routing_key = routing_key

    def format_dynamic(self, **kwargs):
        try:
            exchange = self.exchange.format(**kwargs)
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a exchange name `{self.exchange}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed exchange name `{self.exchange}`. Use an event field name in {{}} "
            )

        try:
            routing_key = self.routing_key.format(**kwargs)
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a routing_key name `{self.routing_key}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed routing_key name `{self.routing_key}`. Use an event field name in {{}} "
            )

        return RabbitMQEventRoute(
            exchange=exchange,
            routing_key=routing_key,
        )


class RabbitMQProducer(Producer):
    def __init__(self,
                 exchanges: list[AbstractExchange],
                 timeout: int | float | None = None) -> None:
        self.exchanges = {exchange.name: exchange for exchange in exchanges}
        self.timeout = timeout

    async def send(self, payload: bytes, route: EventRoute, config: BaseModel | None = None):
        if config is not None and not isinstance(config, RabbitMQEventConfig):
            raise TypeError(
                f"Expected a RabbitMQEventConfig when using RabbitMQProducer got {type(config).__name__}"
            )
        config = config or RabbitMQEventConfig()

        if not isinstance(route, RabbitMQEventRoute):
            raise TypeError(
                f"Expected a RabbitMQEventRoute when using RabbitMQProducer got {type(route).__name__}"
            )

        try:
            await self.exchanges[route.exchange].publish(
                Message(
                    body=payload,
                    delivery_mode=config.delivery_mode,
                    priority=config.priority,
                    expiration=config.expiration,
                    headers=config.headers,
                    content_type=config.content_type,
                    content_encoding=config.content_encoding,
                    correlation_id=config.correlation_id,
                    reply_to=config.reply_to,
                    message_id=config.message_id,
                    timestamp=config.timestamp,
                    type=config.type,
                    user_id=config.user_id,
                    app_id=config.app_id,
                ),
                routing_key=route.routing_key,
                timeout=self.timeout,
            )
        except TimeoutError:
            raise ProducerTimeout()
