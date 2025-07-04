from dispytch.emitter.event import EventBase
from dispytch.emitter.producer import Producer


class EventEmitter:
    def __init__(self, producer: Producer):
        self.producer = producer

    async def emit(self, event: EventBase):
        await self.producer.send(event.__topic__, {
            'id': event.id,
            'type': event.__event_type__,
            'body': event.model_dump(exclude={'id'})
        })
