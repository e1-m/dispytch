from collections import defaultdict

from dispytch.listener.handler import Handler


class HandlerGroup:
    def __init__(self, default_topic: str = None, default_event: str = None):
        self.default_topic = default_topic
        self.default_event = default_event
        self.handlers: dict[str, dict[str, list[Handler]]] = defaultdict(lambda: defaultdict(list))

    def handler(self, *,
                topic: str = None,
                event: str = None,
                retries: int = 0,
                retry_on: type[Exception] = None,
                retry_interval_sec: float = 1.25):
        if topic is None and self.default_topic is None:
            raise TypeError("Topic not specified. "
                            "A topic must be specified "
                            "either via the decorator parameter "
                            "or by setting a default topic in the handler group")

        if event is None and self.default_event is None:
            raise TypeError("Event not specified. "
                            "A event must be specified "
                            "either via the decorator parameter "
                            "or by setting a default event in the handler group")

        def decorator(callback):
            handlers = self.handlers[topic or self.default_topic][event or self.default_event]

            handlers.append(Handler(callback, retries, retry_interval_sec, retry_on))
            return callback

        return decorator
