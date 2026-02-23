from typing import Literal

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    SCENARIO: Literal["raw", "with-io", "with-resource-pool"]

    IN_FLIGHT_MSG_LIMIT_PER_PARTITION: int
    FETCH_INTERVAL_MS: int
    MESSAGE_SIZE_BYTES: int

    BATCH_COMMIT_BATCH_SIZE: int
    BATCH_COMMIT_TIMEOUT_MS: int

    # with-io
    MAX_PROCESSING_TIME_MS: int
    MIN_PROCESSING_TIME_MS: int

    # with-resource-pool
    MAX_RESOURCE_POOL_SIZE: int


config = Config()
