from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    ALLOWED_ORIGINS: list[str] = ["*"]

    RABBIT_MQ_URL: str = "amqp://guest:guest@localhost:5672"


settings = Settings()


class RabbitMQConfig(BaseSettings):
    USER_EVENTS_EXCHANGE_NAME: str = "user.events"
    POST_EVENTS_EXCHANGE_NAME: str = "post.events"

    USER_EVENTS_QUEUE_NAME: str = "user.events.post-service"
    USER_CREATED_ROUTING_KEY: str = "user.created"


rabbit_mq_config = RabbitMQConfig()
