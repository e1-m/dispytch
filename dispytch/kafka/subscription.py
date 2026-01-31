from dispytch.listener.consumer import EventSubscription, Consumer


class KafkaEventSubscription(EventSubscription):
    topic: str = "*"

    def get_segments(self) -> tuple[str, ...]:
        return (self.topic,)
