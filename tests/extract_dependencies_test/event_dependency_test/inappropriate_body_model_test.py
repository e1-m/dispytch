import pytest

from dispytch.di.event import Event
from dispytch.di.extractor import extract_dependencies


class NotBaseModel:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


def test_non_basemodel_event_body():
    """Test function with Event type hint but non-BaseModel event body."""

    def func_with_non_basemodel_event(event_param: Event[NotBaseModel]):
        pass

    with pytest.raises(TypeError):
        extract_dependencies(func_with_non_basemodel_event)
