from collections import defaultdict

from dispytch.listener.handler import Handler


class HandlerGroup:
    def __init__(self):
        self.handlers = defaultdict(dict[str, Handler])

    def handler(self, *,
                topic: str,
                event: str,
                retries: int = 0,
                retry_on: type[Exception] = None,
                retry_interval_sec: float = 1.25):
        def decorator(callback):
            self.handlers[topic][event] = Handler(callback, retries, retry_interval_sec, retry_on)
            return callback

        return decorator
