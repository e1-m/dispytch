import pytest
from tests.integration.backends.kafka import *
from tests.integration.backends.rabbitmq import *
from tests.integration.backends.redis_ import *


@pytest.fixture(params=[
    pytest.param("kafka", id="kafka"),
    pytest.param("rabbitmq", id="rabbitmq"),
    pytest.param("redis", id="redis"),
])
def backend_name(request) -> str:
    return request.param


@pytest.fixture
def backend(backend_name, request):
    return request.getfixturevalue(f"backend_{backend_name}")


@pytest.fixture(params=[
    pytest.param("kafka_params", id="kafka.params"),
    pytest.param("rabbitmq_params", id="rabbitmq.params"),
    pytest.param("redis_params", id="redis.params"),
])
def backend_params_name(request) -> str:
    return request.param


@pytest.fixture
def backend_params(backend_params_name, request):
    return request.getfixturevalue(f"backend_{backend_params_name}")


@pytest.fixture
def listener_start_up_time():
    return 0.5


@pytest.fixture
def event_processing_delay():
    return 0.5
