import pytest
from dispytch.kafka import KafkaEventConfig

from mocks import *


@pytest.mark.asyncio
async def test_send_with_no_config(kafka_producer, mock_kafka_producer):
    """Test send method with no config provided"""
    topic = "test_topic"
    payload = {"key": "value", "id": 123}

    await kafka_producer.send(topic, payload)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] is None


@pytest.mark.asyncio
async def test_send_with_empty_config(kafka_producer, mock_kafka_producer, mock_serializer):
    """Test send method with empty KafkaEventConfig"""
    topic = "test_topic"
    payload = {"key": "value", "id": 123}
    config = KafkaEventConfig()

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] is None


@pytest.mark.asyncio
async def test_send_with_simple_partition_key(kafka_producer, mock_kafka_producer):
    """Test send method with simple partition key"""
    topic = "test_topic"
    payload = {"user_id": "user123", "message": "hello"}
    config = KafkaEventConfig(partition_by="user_id")

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] == "user123"


@pytest.mark.asyncio
async def test_send_with_nested_partition_key(kafka_producer, mock_kafka_producer):
    """Test send method with nested partition key"""
    topic = "test_topic"
    payload = {
        "user": {
            "id": "user123",
            "name": "John Doe"
        },
        "message": "hello"
    }
    config = KafkaEventConfig(partition_by="user.id")

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] == "user123"


@pytest.mark.asyncio
async def test_send_with_deeply_nested_partition_key(kafka_producer, mock_kafka_producer):
    """Test send method with deeply nested partition key"""
    topic = "test_topic"
    payload = {
        "event": {
            "user": {
                'id': "user123",
                "profile": {
                    "id": "profile123",
                    "name": "John Doe"
                }
            }
        }
    }
    config = KafkaEventConfig(partition_by="event.user.profile.id")

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] == "profile123"


@pytest.mark.asyncio
async def test_send_with_integer_partition_key(kafka_producer, mock_kafka_producer):
    """Test send method with integer partition key value"""
    topic = "test_topic"
    payload = {"id": 123, "data": "test"}
    config = KafkaEventConfig(partition_by="id")

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] == 123


@pytest.mark.asyncio
async def test_send_with_complex_nested_structure(kafka_producer, mock_kafka_producer):
    """Test send with complex nested structure and deep partition key"""
    topic = "test_topic"
    payload = {
        "event": {
            "timestamp": "2023-01-01T00:00:00Z",
            "user": {
                "profile": {
                    "id": "profile123",
                    "settings": {
                        "notifications": True
                    }
                },
                "account": {
                    "type": "premium"
                }
            }
        },
        "metadata": {
            "source": "web",
            "version": "1.0"
        }
    }
    config = KafkaEventConfig(partition_by="event.user.profile.id")

    await kafka_producer.send(topic, payload, config)

    args, kwargs = mock_kafka_producer.send_and_wait.call_args

    assert kwargs["topic"] == topic
    assert kwargs["value"] == "serialized_data"
    assert kwargs["key"] == "profile123"
