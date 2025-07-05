from dispytch.emitter.event import EventBase
from dispytch.emitter.producer import Producer


def _extract_partition_key(event: dict, partition_key: str):
    parts = partition_key.split('.')
    current = event

    for i, part in enumerate(parts):
        if not isinstance(current, dict):
            raise ValueError(
                f"Expected a nested structure at '{'.'.join(parts[:i])}', got {type(current).__name__}"
            )
        try:
            current = current[part]
        except KeyError:
            raise KeyError(f"Partition key '{partition_key}' not found in event")

    return current


class EventEmitter:
    def __init__(self, producer: Producer):
        self.producer = producer

    async def emit(self, event: EventBase):
        event_body = event.model_dump(exclude={'id'})
        await self.producer.send(
            topic=event.__topic__,
            payload={
                'id': event.id,
                'type': event.__event_type__,
                'body': event_body
            },
            key=_extract_partition_key(event_body, event.__partition_by__) if event.__partition_by__ else None
        )
