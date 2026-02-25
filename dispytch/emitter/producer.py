from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProducerTimeout(Exception):
    pass


class EventRoute(BaseModel, ABC):
    def format_dynamic(self, **kwargs) -> "EventRoute":
        updates = {}

        for attr_name, attr_value in self.model_dump().items():
            if isinstance(attr_value, str):
                try:
                    updates[attr_name] = attr_value.format(**kwargs)
                except KeyError as e:
                    raise RuntimeError(
                        f"Missing an event field `{e.args[0]}` "
                        f"used to form a {attr_name} name `{attr_value}`"
                    ) from e
                except IndexError:
                    raise RuntimeError(
                        f"Malformed {attr_name} name `{attr_value}`. Use an event field name in {{}} "
                    )

        return self.model_copy(update=updates)


class Producer(ABC):
    @abstractmethod
    async def send(self, payload: bytes, route: EventRoute, config: BaseModel | None = None): ...
