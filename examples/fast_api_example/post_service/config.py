from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    ALLOWED_ORIGINS: list[str] = ["*"]

    RABBIT_MQ_URL: str = "amqp://guest:guest@localhost:5672"


settings = Settings()


class EventHandlingConfig(BaseSettings):
    USER_EVENTS_TOPIC: str = "user_events"


event_handling_config = EventHandlingConfig()


class RabbitMQConfig(BaseSettings):
    USER_EVENTS_EXCHANGE_NAME: str = "user_events_exchange"
    POST_EVENTS_EXCHANGE_NAME: str = "post_events_exchange"

    # the queue name should be used as `topic` in a handler decorator in version 0.9.1
    # from version 0.10.0 onwards, the emitting side's `__topic__` is used instead
    USER_EVENTS_QUEUE_NAME: str = event_handling_config.USER_EVENTS_TOPIC
    # the routing key should be the same as emitting side's `__topic__`
    USER_EVENTS_ROUTING_KEY: str = event_handling_config.USER_EVENTS_TOPIC
    # now they coincide,
    # but in principle you can use any queue name as long as the queue
    # is bound using the correct routing key (i.e., the producer side’s `__topic__`)


rabbit_mq_config = RabbitMQConfig()
