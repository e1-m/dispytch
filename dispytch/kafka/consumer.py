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
        self._is_running = False
        self._is_data_available: asyncio.Event | None = None
        self._fetch_task = None

    async def start(self):
        if self._is_running:
            logger.warning("Attempting to start an already running consumer.")
            return

        existing_topics = self.consumer.subscription()
        if not existing_topics:
            raise RuntimeError("Consumer must be subscribed to topics before listening.")
        if self.consumer._enable_auto_commit:  # noqa
            raise RuntimeError("Consumer must have auto commit disabled before listening.")

        self.consumer.subscribe(topics=list(existing_topics), listener=self)
        await self.consumer.start()

        self._is_data_available = asyncio.Event()
        self._is_running = True
        self._fetch_task = asyncio.create_task(self._fetch_loop())

    async def stop(self):
        if not self._is_running:
            logger.warning("Attempting to stop a non-running consumer.")
            return

        self._is_running = False

        if self._is_data_available:
            self._is_data_available.set()

        if self._fetch_task:
            self._fetch_task.cancel()

            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass

        await self.consumer.stop()

    async def listen(self) -> AsyncIterator[Message]:
        cycle_idx = 0

        while self._is_running:
            await self._is_data_available.wait()

            # Back to sleep in case a rebalance occurred
            if not (partitions := list(self._queues.keys())):
                self._is_data_available.clear()
                continue

            yielded_in_cycle = False

            for _ in range(len(partitions)):
                tp = partitions[cycle_idx % len(partitions)]
                cycle_idx += 1

                queue = self._queues.get(tp)
                if queue is not None and not queue.empty():
                    kafka_msg = queue.get_nowait()

                    msg = Message(
                        subscription=KafkaEventSubscription(topic=kafka_msg.topic),
                        payload=kafka_msg.value
                    )

                    self._waiting_for_commit[msg.id] = _MessageCommitInfo(
                        tp=tp,
                        offset=kafka_msg.offset
                    )

                    if tp not in self._offset_trackers:
                        self._offset_trackers[tp] = OffsetTracker(kafka_msg.offset)

                    yield msg
                    yielded_in_cycle = True
                    break

            if not yielded_in_cycle:
                self._is_data_available.clear()

    async def ack(self, message: Message):
        commit_info = self._waiting_for_commit.pop(message.id, None)
        if not commit_info:
            return

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
        while self._is_running:
            fetched_any = False

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

                if records:
                    fetched_any = True

                    if tp not in self._queues:
                        self._queues[tp] = asyncio.Queue()

                    for record in records:
                        self._queues[tp].put_nowait(record)
                        self._in_flight_count[tp] += 1

            if fetched_any:
                self._is_data_available.set()

            await asyncio.sleep(self.fetch_interval_ms / 1000.0)
