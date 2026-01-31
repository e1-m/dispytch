from dispytch.listener.consumer import EventSubscription


class RabbitMQEventSubscription(EventSubscription):
    exchange: str = "*"
    queue: str = "*"
    routing_key: str = "*"

    def get_segments(self) -> tuple[str, ...]:
        return self.exchange, self.queue, self.routing_key
