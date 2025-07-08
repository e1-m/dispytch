import aio_pika

from post_service.config import rabbit_mq_config, settings


class RabbitMQResources:
    def __init__(self,
                 connection,
                 post_exchange,
                 user_exchange,
                 user_queue):
        self.connection = connection
        self.post_exchange = post_exchange
        self.user_exchange = user_exchange
        self.user_queue = user_queue


async def init_rabbit_mq() -> RabbitMQResources:
    connection = await aio_pika.connect(settings.RABBIT_MQ_URL)
    channel = await connection.channel()
    user_exchange = await channel.declare_exchange(rabbit_mq_config.USER_EVENTS_EXCHANGE_NAME,
                                                   aio_pika.ExchangeType.DIRECT)
    post_exchange = await channel.declare_exchange(rabbit_mq_config.POST_EVENTS_EXCHANGE_NAME,
                                                   aio_pika.ExchangeType.DIRECT)

    user_queue = await channel.declare_queue(rabbit_mq_config.USER_EVENTS_QUEUE_NAME)
    await user_queue.bind(user_exchange, rabbit_mq_config.USER_EVENTS_ROUTING_KEY)

    return RabbitMQResources(
        connection,
        post_exchange,
        user_exchange,
        user_queue)
