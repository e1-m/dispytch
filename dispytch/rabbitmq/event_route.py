from dispytch.emitter.producer import EventRoute


class RabbitMQEventRoute(EventRoute):
    exchange: str
    routing_key: str

    def format_dynamic(self, **kwargs):
        try:
            exchange = self.exchange.format(**kwargs)
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a exchange name `{self.exchange}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed exchange name `{self.exchange}`. Use an event field name in {{}} "
            )

        try:
            routing_key = self.routing_key.format(**kwargs)
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a routing_key name `{self.routing_key}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed routing_key name `{self.routing_key}`. Use an event field name in {{}} "
            )

        return RabbitMQEventRoute(
            exchange=exchange,
            routing_key=routing_key,
        )
