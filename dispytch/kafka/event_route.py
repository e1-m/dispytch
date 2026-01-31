from dispytch.emitter.producer import EventRoute


class KafkaEventRoute(EventRoute):
    topic: str

    def format_dynamic(self, **kwargs):
        try:
            return KafkaEventRoute(topic=self.topic.format(**kwargs))
        except KeyError as e:
            raise RuntimeError(
                f"Missing an event field `{e.args[0]}` "
                f"used to form a topic name `{self.topic}`") from e
        except IndexError:
            raise RuntimeError(
                f"Malformed topic name `{self.topic}`. Use an event field name in {{}} "
            )
