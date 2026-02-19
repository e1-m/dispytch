from dataclasses import dataclass
from typing import AsyncIterator
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, TopicPartition, ConsumerRebalanceListener

from dispytch.dispatcher.consumer import Consumer, Message, EventSubscription
from dispytch.kafka.batch_processor import BatchProcessor
from dispytch.kafka.offset_tracker import OffsetTracker

logger = logging.getLogger(__name__)


class KafkaEventSubscription(EventSubscription):
    topic: str = "*"


@dataclass
class _MessageCommitInfo:
    tp: TopicPartition
    offset: int


class KafkaConsumer(Consumer, ConsumerRebalanceListener):
    def __init__(self, consumer: AIOKafkaConsumer, batch_timeout_ms: int = 1000, batch_size: int = 10):
        self.consumer = consumer
        self.batch_processor = BatchProcessor(
            handler=consumer.commit,
            batch_timeout_ms=batch_timeout_ms,
            batch_size=batch_size
        )
        self._waiting_for_commit: dict[UUID, _MessageCommitInfo] = {}
        self._offset_tracker: dict[TopicPartition, OffsetTracker] = {}

    async def start(self):
        existing_topics = self.consumer.subscription()
        if not existing_topics:
            raise RuntimeError("Consumer must be subscribed to topics before listening.")
        if self.consumer._enable_auto_commit is True:
            raise RuntimeError("Consumer must have auto commit disabled before listening.")

        self.consumer.subscribe(topics=list(existing_topics), listener=self)
        await self.consumer.start()

    async def listen(self) -> AsyncIterator[Message]:
        async for message in self.consumer:
            msg = Message(subscription=KafkaEventSubscription(topic=message.topic),
                          payload=message.value)

            tp = TopicPartition(message.topic, message.partition)

            self._waiting_for_commit[msg.id] = _MessageCommitInfo(
                tp=tp,
                offset=message.offset
            )

            if tp not in self._offset_tracker:
                self._offset_tracker[tp] = OffsetTracker(message.offset)

            yield msg

    async def ack(self, message: Message):
        commit_info = self._waiting_for_commit.pop(message.id)

        # In case the partition was revoked before the message was processed
        offset_tracker = self._offset_tracker.get(commit_info.tp, None)
        if offset_tracker is None:
            return

        offset_to_commit = offset_tracker.mark_processed(commit_info.offset)
        if offset_to_commit is not None:
            await self.batch_processor.add(commit_info.tp, offset_to_commit)

    async def on_partitions_revoked(self, revoked: list[TopicPartition]):
        for tp in revoked:
            if tp in self._offset_tracker:
                self._offset_tracker.pop(tp)

    async def on_partitions_assigned(self, assigned: list[TopicPartition]):
        ...
