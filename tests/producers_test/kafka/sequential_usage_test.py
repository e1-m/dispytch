import pytest
from unittest.mock import AsyncMock, Mock

from dispytch.kafka import KafkaProducer, KafkaEventConfig
from mocks import *


@pytest.mark.asyncio
async def test_send_multiple_calls_with_different_configs(kafka_producer, mock_kafka_producer, mock_serializer):
    """Test multiple send calls with different configurations"""
    topic = "test_topic"

    await kafka_producer.send(topic, {"id": 1, "message": "first"})

    await kafka_producer.send(
        topic,
        {"id": 2, "message": "second"},
        KafkaEventConfig(partition_by="id")
    )

    await kafka_producer.send(
        topic,
        {"user": {"id": 3}, "message": "third"},
        KafkaEventConfig(partition_by="user.id")
    )

    assert mock_kafka_producer.send_and_wait.call_count == 3

    calls = mock_kafka_producer.send_and_wait.call_args_list
    assert calls[0][1]["key"] is None
    assert calls[1][1]["key"] == 2
    assert calls[2][1]["key"] == 3


@pytest.mark.asyncio
async def test_send_with_same_config_different_payloads(kafka_producer, mock_kafka_producer, mock_serializer):
    """Test send with same config but different payloads"""
    topic = "test_topic"
    config = KafkaEventConfig(partition_by="user_id")

    payloads = [
        {"user_id": "user1", "action": "login"},
        {"user_id": "user2", "action": "logout"},
        {"user_id": "user3", "action": "purchase"}
    ]

    for payload in payloads:
        await kafka_producer.send(topic, payload, config)

    assert mock_kafka_producer.send_and_wait.call_count == 3

    calls = mock_kafka_producer.send_and_wait.call_args_list
    assert calls[0][1]["key"] == "user1"
    assert calls[1][1]["key"] == "user2"
    assert calls[2][1]["key"] == "user3"
