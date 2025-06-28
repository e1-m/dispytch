class DependencyResolutionError(Exception):
    pass


class CyclicDependencyError(DependencyResolutionError):
    pass


class InvalidGeneratorError(DependencyResolutionError):
    pass
