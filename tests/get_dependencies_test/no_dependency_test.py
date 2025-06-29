import inspect

from src.di.solv import _get_dependencies as get_dependencies  # noqa


def test_empty_signature():
    """Test function with no parameters."""

    def empty_func():
        pass

    sig = inspect.signature(empty_func)
    result = get_dependencies(sig)

    assert result == {}


def test_no_dependencies():
    """Test function with regular parameters but no dependencies."""

    def regular_func(a: int, b: str, c=None, d=1):
        pass

    sig = inspect.signature(regular_func)
    result = get_dependencies(sig)

    assert result == {}
