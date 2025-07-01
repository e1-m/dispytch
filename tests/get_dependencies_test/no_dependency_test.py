from src.di.solv.extractor import _get_user_defined_dependencies as get_dependencies


def test_empty_signature():
    """Test function with no parameters."""

    def empty_func():
        pass

    result = get_dependencies(empty_func)

    assert result == {}


def test_no_dependencies():
    """Test function with regular parameters but no dependencies."""

    def regular_func(a: int, b: str, c=None, d=1):
        pass

    result = get_dependencies(regular_func)

    assert result == {}
