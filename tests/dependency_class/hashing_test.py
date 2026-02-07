from dispytch.di.dependency import Dependency


def test_dependency_hashing_with_same_function():
    def create_service():
        return "service"

    dep1 = Dependency(create_service)
    dep2 = Dependency(create_service)

    assert hash(dep1) == hash(dep2)


def test_dependency_hashing_with_different_functions():
    def create_first_service():
        return "first_service"

    def create_second_service():
        return "second_service"

    dep1 = Dependency(create_first_service)
    dep2 = Dependency(create_second_service)

    assert hash(dep1) != hash(dep2)


def test_dependency_hashing_with_different_functions_with_the_same_meaning():
    dep1 = Dependency(lambda: "service")
    dep2 = Dependency(lambda: "service")

    assert hash(dep1) != hash(dep2)
