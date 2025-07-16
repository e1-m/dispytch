from typing import Annotated

from dispytch.di.extractor import extract_dependencies
from dispytch.di.dependency import Dependency


def test_annotated_dependency():
    """Test parameter with Annotated type containing Dependency."""
    dep = Dependency(lambda: "test")

    def func_with_annotated(service: Annotated[str, dep]):
        pass

    result = extract_dependencies(func_with_annotated)

    assert len(result) == 1
    assert "service" in result
    assert result["service"] == dep


def test_annotated_multiple_metadata_with_dependency():
    """Test Annotated with multiple metadata items including Dependency."""
    dep = Dependency(lambda: "test")
    other_meta = "some_other_metadata"

    def func_with_meta(service: Annotated[int, other_meta, dep, "more_meta"]):
        pass

    result = extract_dependencies(func_with_meta)

    assert len(result) == 1
    assert result["service"] == dep


def test_annotated_no_dependency_in_metadata():
    """Test Annotated with metadata but no Dependency objects."""

    def func_with_meta_no_dep(service: Annotated[str, "metadata", 42]):
        pass

    result = extract_dependencies(func_with_meta_no_dep)

    assert result == {}


def test_annotated_first_dependency_wins():
    """Test that first Dependency in Annotated metadata is used."""
    dep1 = Dependency(lambda: "test1")
    dep2 = Dependency(lambda: "test2")

    def func_with_multiple_deps_in_annotation(
            param: Annotated[str, dep1, dep2]
    ):
        pass

    result = extract_dependencies(func_with_multiple_deps_in_annotation)

    assert len(result) == 1
    assert result["param"] == dep1  # First dependency should win
