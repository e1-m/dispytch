import pytest
from unittest.mock import AsyncMock, Mock

from dispytch.producers.kafka import KafkaProducer


@pytest.fixture
def mock_kafka_producer():
    producer = AsyncMock()
    producer.send = AsyncMock()
    return producer


@pytest.fixture
def mock_serializer():
    serializer = Mock()
    serializer.serialize = Mock(return_value="serialized_data")
    return serializer


@pytest.fixture
def kafka_producer(mock_kafka_producer, mock_serializer):
    return KafkaProducer(mock_kafka_producer, mock_serializer)
