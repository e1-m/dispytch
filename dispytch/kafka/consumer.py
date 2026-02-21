import asyncio
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
    def __init__(self,
                 consumer: AIOKafkaConsumer,
                 in_flight_msg_limit_per_partition: int = 100,
                 fetch_interval_ms: int = 100,
                 batch_timeout_ms: int = 1000,
                 batch_size: int = 10):
        self.consumer = consumer
        self.in_flight_msg_limit_per_partition = in_flight_msg_limit_per_partition
        self.fetch_interval_ms = fetch_interval_ms
        self._batch_processor = BatchProcessor(
            handler=self._batch_commit,
            batch_timeout_ms=batch_timeout_ms,
            batch_size=batch_size
        )
        self._waiting_for_commit: dict[UUID, _MessageCommitInfo] = {}
        self._offset_trackers: dict[TopicPartition, OffsetTracker] = {}
        self._in_flight_count: dict[TopicPartition, int] = {}
        self._queues: dict[TopicPartition, asyncio.Queue] = {}
        self._running = False

    async def start(self):
        existing_topics = self.consumer.subscription()
        if not existing_topics:
            raise RuntimeError("Consumer must be subscribed to topics before listening.")
        if self.consumer._enable_auto_commit:  # noqa
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

            if tp not in self._offset_trackers:
                self._offset_trackers[tp] = OffsetTracker(message.offset)

            yield msg

    async def ack(self, message: Message):
        commit_info = self._waiting_for_commit.pop(message.id)
        tp = commit_info.tp

        # In case the partition was revoked before the message was processed
        if tp not in self._offset_trackers or tp not in self._in_flight_count:
            return

        self._in_flight_count[tp] -= 1

        offset_to_commit = self._offset_trackers[tp].mark_processed(commit_info.offset)
        if offset_to_commit is not None:
            await self._batch_processor.add((tp, offset_to_commit + 1))

    async def on_partitions_revoked(self, revoked: list[TopicPartition]):
        for tp in revoked:
            if tp in self._offset_trackers:
                self._offset_trackers.pop(tp)
            if tp in self._in_flight_count:
                self._in_flight_count.pop(tp)
            if tp in self._queues:
                self._queues.pop(tp)

    async def on_partitions_assigned(self, assigned: list[TopicPartition]):
        ...

    async def _batch_commit(self, batch: list[tuple[TopicPartition, int]]):
        await self.consumer.commit({tp: offset for tp, offset in batch})

    async def _fetch_loop(self):
        while self._running:
            for tp in self.consumer.assignment():
                # Initialize partition in flight count if tp is seen for the first time
                if tp not in self._in_flight_count:
                    self._in_flight_count[tp] = 0

                max_records_to_fetch = self.in_flight_msg_limit_per_partition - self._in_flight_count[tp]
                # Skip if the limit for the partition is reached
                if max_records_to_fetch <= 0:
                    continue

                batches = await self.consumer.getmany(tp, timeout_ms=0, max_records=max_records_to_fetch)
                records = batches.get(tp, [])

                for record in records:
                    # Initialize the partition queue if tp is seen for the first time
                    if tp not in self._queues:
                        self._queues[tp] = asyncio.Queue()

                    self._queues[tp].put_nowait(record)
                    self._in_flight_count[tp] += 1

            await asyncio.sleep(self.fetch_interval_ms / 1000.0)
