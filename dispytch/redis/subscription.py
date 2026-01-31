from dispytch.listener.consumer import EventSubscription


class RedisEventSubscription(EventSubscription):
    channel: str = "*"

    def get_segments(self) -> tuple[str, ...]:
        return (self.channel,)
