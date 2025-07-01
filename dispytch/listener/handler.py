from typing import Callable, Any, Sequence


class Handler:
    def __init__(self, func: Callable[..., Any],
                 retries: int = 0,
                 retry_on: Sequence[type[Exception]] = None):
        self.retries = abs(retries)
        self.retry_on = retry_on
        self.func = func

    def __call__(self, *args, **kwargs):
        for attempt in range(self.retries + 1):  # noqa
            try:
                return self.func(*args, **kwargs)
            except Exception as e:
                should_retry = (
                        self.retry_on is None or
                        isinstance(e, tuple(self.retry_on))
                )

                if attempt == self.retries or not should_retry:
                    raise e
