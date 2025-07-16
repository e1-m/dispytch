from collections import defaultdict

from dispytch.listener.handler import Handler


class HandlerGroup:
    """
       A registry for grouping and configuring event handlers by topic and event type.

       Args:
           default_topic (str, optional): The default topic to register handlers under,
               used when not specified in the decorator.
           default_event (str, optional): The default event type to register handlers under,
               used when not specified in the decorator.
       """

    def __init__(self, default_topic: str = None, default_event: str = None):
        self.default_topic = default_topic
        self.default_event = default_event
        self.handlers: dict[str, dict[str, list[Handler]]] = defaultdict(lambda: defaultdict(list))

    def handler(self, *,
                topic: str = None,
                event: str = None,
                retries: int = 0,
                retry_on: type[Exception] = None,
                retry_interval: float = 1.25):
        """
           Decorator to register a handler function for a specific topic and event type.

           Args:
               topic (str, optional): The topic this handler listens to. If not set,
                   `default_topic` from the HandlerGroup will be used.
               event (str, optional): The event type this handler handles. If not set,
                   `default_event` from the HandlerGroup will be used.
               retries (int, optional): Number of times to retry the handler on failure.
                   Defaults to 0 (no retries).
               retry_on (type[Exception], optional): Exception type to trigger retries.
                   If not set, retries will be attempted on any exception.
               retry_interval (float, optional): Delay in seconds between retries.
                   Defaults to 1.25 seconds.

           Raises:
               TypeError: If neither topic nor default_topic in a handler group is specified.
               TypeError: If neither event nor default_event in a handler group is specified.
           """
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

            handlers.append(Handler(callback, topic, retries, retry_interval, retry_on))
            return callback

        return decorator
