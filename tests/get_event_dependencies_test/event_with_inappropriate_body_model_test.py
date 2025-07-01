import pytest

from src.di.models import Event
from src.di.solv.extractor import _get_event_requests_as_dependencies as get_event_dependencies


class NotBaseModel:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


def test_non_basemodel_event_body():
    """Test function with Event type hint but non-BaseModel event body."""

    def func_with_non_basemodel_event(event_param: Event[NotBaseModel]):
        pass

    with pytest.raises(TypeError):
        get_event_dependencies(func_with_non_basemodel_event)
