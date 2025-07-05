import pytest
from pydantic import BaseModel

from dispytch.producers.kafka import KafkaEventConfig
from mocks import *


class InvalidConfig(BaseModel):
    some_field: str = "test"


@pytest.mark.asyncio
async def test_send_with_null_partition_key(kafka_producer):
    """Test send method with null partition key value"""
    topic = "test_topic"
    payload = {"id": None, "data": "test"}
    config = KafkaEventConfig(partition_by="id")

    with pytest.raises(ValueError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_list_partition_key(kafka_producer):
    """Test send method with list partition key value"""
    topic = "test_topic"
    payload = {"tags": ["tag1", "tag2"], "data": "test"}
    config = KafkaEventConfig(partition_by="tags")

    with pytest.raises(ValueError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_invalid_config_type(kafka_producer):
    """Test send method with invalid config type"""
    topic = "test_topic"
    payload = {"key": "value"}
    config = InvalidConfig()

    with pytest.raises(ValueError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_missing_partition_key(kafka_producer):
    """Test send method when partition key is missing from payload"""
    topic = "test_topic"
    payload = {"message": "hello"}
    config = KafkaEventConfig(partition_by="user_id")

    with pytest.raises(KeyError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_missing_nested_partition_key(kafka_producer):
    """Test send method when nested partition key is missing from payload"""
    topic = "test_topic"
    payload = {"user": {"name": "John"}}
    config = KafkaEventConfig(partition_by="user.id")

    with pytest.raises(KeyError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_missing_intermediate_key(kafka_producer):
    """Test send method when intermediate key in nested path is missing"""
    topic = "test_topic"
    payload = {"data": "test"}
    config = KafkaEventConfig(partition_by="user.profile.id")

    with pytest.raises(KeyError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_non_dict_intermediate_value(kafka_producer):
    """Test send method when intermediate value in partition key path is not a dict"""
    topic = "test_topic"
    payload = {"user": "john_doe", "message": "hello"}
    config = KafkaEventConfig(partition_by="user.id")

    with pytest.raises(ValueError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_list_intermediate_value(kafka_producer):
    """Test send method when intermediate value in partition key path is a list"""
    topic = "test_topic"
    payload = {"users": ["user1", "user2"], "message": "hello"}
    config = KafkaEventConfig(partition_by="users.id")

    with pytest.raises(ValueError):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_number_intermediate_value(kafka_producer):
    """Test send method when intermediate value in partition key path is a number"""
    topic = "test_topic"
    payload = {"user": 123, "message": "hello"}
    config = KafkaEventConfig(partition_by="user.id")

    with pytest.raises(ValueError, match="Expected a nested structure at 'user', got int"):
        await kafka_producer.send(topic, payload, config)


@pytest.mark.asyncio
async def test_send_with_trailing_dot(kafka_producer):
    """Test send method with trailing dot """
    topic = "test_topic"
    payload = {"user": {"id": 123}, "message": "hello"}
    config = KafkaEventConfig(partition_by="user.")

    with pytest.raises(KeyError):
        await kafka_producer.send(topic, payload, config)
