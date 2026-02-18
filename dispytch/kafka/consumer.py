from dataclasses import dataclass
from typing import AsyncIterator
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, TopicPartition, ConsumerRebalanceListener

from dispytch.dispatcher.consumer import Consumer, Message, EventSubscription

logger = logging.getLogger(__name__)


class KafkaEventSubscription(EventSubscription):
    topic: str = "*"


@dataclass
class _MessageCommitInfo:
    tp: TopicPartition
    offset: int


class OffsetManager:
    def __init__(self, starting_offset: int = -1):
        self.next_expected_offset = starting_offset
        self.last_committed = starting_offset - 1
        self.completed_pool = set()

    def mark_processed(self, offset: int):
        if offset < self.next_expected_offset:
            return None

        self.completed_pool.add(offset)

        if offset != self.next_expected_offset:
            return None

        while self.next_expected_offset in self.completed_pool:
            self.completed_pool.remove(self.next_expected_offset)

            self.last_committed = self.next_expected_offset
            self.next_expected_offset += 1

        return self.last_committed


class KafkaConsumer(Consumer, ConsumerRebalanceListener):
    def __init__(self, consumer: AIOKafkaConsumer):
        self.consumer = consumer
        self._waiting_for_commit: dict[UUID, _MessageCommitInfo] = {}
        self._offset_manager: dict[TopicPartition, OffsetManager] = {}

    async def start(self):
        existing_topics = self.consumer.subscription()
        if not existing_topics:
            raise RuntimeError("Consumer must be subscribed to topics before listening.")

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

            if tp not in self._offset_manager:
                self._offset_manager[tp] = OffsetManager(message.offset)

            yield msg

    async def ack(self, message: Message):
        commit_info = self._waiting_for_commit.pop(message.id)

        # In case the partition was revoked before the message was processed
        offset_manager = self._offset_manager.get(commit_info.tp, None)
        if offset_manager is None:
            return

        offset_to_commit = offset_manager.mark_processed(commit_info.offset)
        if offset_to_commit is not None:
            logger.info(f"Committing offset {offset_to_commit}")
            await self.consumer.commit({commit_info.tp: offset_to_commit + 1})

    async def on_partitions_revoked(self, revoked: list[TopicPartition]):
        for tp in revoked:
            if tp in self._offset_manager:
                self._offset_manager.pop(tp)

    async def on_partitions_assigned(self, assigned: list[TopicPartition]):
        ...
