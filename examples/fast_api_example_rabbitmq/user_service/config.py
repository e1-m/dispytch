from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    ALLOWED_ORIGINS: list[str] = ["*"]

    RABBIT_MQ_URL: str = "amqp://guest:guest@localhost:5672"


settings = Settings()


class RabbitMQConfig(BaseSettings):
    USER_EVENTS_EXCHANGE_NAME: str = "user.events"
    POST_EVENTS_EXCHANGE_NAME: str = "post.events"

    POST_EVENTS_QUEUE_NAME: str = "post.events.user-service"
    POST_CREATED_ROUTING_KEY: str = "post.created"


rabbit_mq_config = RabbitMQConfig()
