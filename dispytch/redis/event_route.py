from dispytch.emitter.producer import EventRoute


class RedisEventRoute(EventRoute):
    def __init__(self, channel: str):
        self.channel = channel

    def format_dynamic(self, **kwargs):
        try:
            return RedisEventRoute(channel=self.channel.format(**kwargs))
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a channel name `{self.channel}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed channel name `{self.channel}`. Use an event field name in {{}} "
            )
