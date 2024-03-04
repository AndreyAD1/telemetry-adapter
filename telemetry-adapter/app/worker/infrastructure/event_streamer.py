from abc import ABC, abstractmethod
from datetime import datetime, UTC
import logging
from enum import Enum
from typing import Union, Optional
from uuid import uuid4

import psycopg.errors
from psycopg.rows import class_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, UUID4, AwareDatetime, NonNegativeInt

from app.worker.infrastructure.clients.exceptions import KinesisClientException
from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.types import Submission, NewProcess, NetworkConnection

logger = logging.getLogger(__name__)


class EventStreamer(ABC):
    @abstractmethod
    def downstream_submission(self, submission: Submission):
        pass


class KinesisEvent(BaseModel):
    id: UUID4
    event_type: str
    device_id: UUID4
    processing_timestamp: AwareDatetime
    event_details: Union[NewProcess, NetworkConnection]


class StatusEnum(Enum):
    pending = "pending"
    processed = "processed"


class StoredSubmission(BaseModel):
    id: UUID4
    status: StatusEnum
    number_of_delivered_events: NonNegativeInt
    sequence_number: Optional[str]


class KinesisStreamer(EventStreamer):
    def __init__(self, kinesis_client: KinesisClient, pg_connection_pool: AsyncConnectionPool):
        self.stream_name = "events"
        self.kinesis_client = kinesis_client
        self.connection_pool = pg_connection_pool

    async def downstream_submission(self, submission: Submission) -> bool:
        process_events = [("new_process", p) for p in submission.events.new_process]
        connection_events = [("network_connection", p) for p in submission.events.network_connection]
        all_events = process_events + connection_events

        async with self.connection_pool.connection() as conn:
            await conn.set_autocommit(True)
            async with conn.cursor(row_factory=class_row(StoredSubmission)) as cur:
                delivered_events_number, sequence_number, is_success = await self._get_current_submission_status(
                    cur,
                    submission.submission_id,
                    len(all_events)
                )
                if is_success is not None:
                    return is_success

            logger.debug(f"downstream a submission {submission}")
            events = []
            for event_type, event_details in all_events[delivered_events_number:]:
                event = KinesisEvent(
                    id=uuid4(),
                    event_type=event_type,
                    device_id=submission.device_id,
                    processing_timestamp=datetime.now(UTC),
                    event_details=event_details
                )
                events.append(event)

            is_success = False
            for i, event in enumerate(events):
                json_event = event.model_dump_json()
                try:
                    async with conn.transaction():
                        await conn.execute(
                            "UPDATE submissions SET number_of_delivered_events=%s, sequence_number=%s WHERE id=%s",
                            (delivered_events_number, sequence_number, submission.submission_id)
                        )
                        try:
                            sequence_number = await self.kinesis_client.put_record(
                                self.stream_name,
                                json_event.encode(),
                                str(event.device_id),
                                sequence_number
                            )
                        except KinesisClientException:
                            await conn.rollback()
                            break

                        # if the last event is delivered, we want to delete
                        #  the message from SQS even when DB commit fails
                        if i == len(events) - 1:
                            is_success = True
                        delivered_events_number += 1
                        logger.debug(f"receive a sequence number {sequence_number} for {json_event}")
                except psycopg.OperationalError as ex:
                    logger.warning(f"DB error while sending the event {event}: {ex}")
                    break

            await conn.execute(
                "UPDATE submissions SET number_of_delivered_events=%s, sequence_number=%s, "
                "status='processed' WHERE id=%s",
                (delivered_events_number, sequence_number, submission.submission_id,)
            )

        return is_success

    @staticmethod
    async def _get_current_submission_status(cur, submission_id, event_number):
        delivered_events_number = 0
        sequence_number = None

        await cur.execute(
            "SELECT * FROM submissions WHERE id = %s",
            (submission_id,)
        )
        stored_submission = await cur.fetchone()
        if stored_submission:
            logger.debug(f"query_result {stored_submission}")
            if stored_submission.status == StatusEnum.pending.value:
                return delivered_events_number, sequence_number, False
            if stored_submission.number_of_delivered_events == len(event_number):
                return delivered_events_number, sequence_number, True
            delivered_events_number = stored_submission.number_of_delivered_events
            sequence_number = stored_submission.sequence_number
            cur.execute(
                "UPDATE submissions SET status='pending' "
                "WHERE id=%s AND status='processed' AND delivered_events_number=%s",
                (submission_id, delivered_events_number)
            )
            # another worker is processing an event
            if cur.rowcount == 0:
                return delivered_events_number, sequence_number, False
        else:
            # create a new pending submission
            try:
                await cur.execute(
                    "INSERT INTO submissions (id, status, number_of_delivered_events) "
                    "VALUES (%s, %s, %s)",
                    (submission_id, "pending", 0)
                )
            except psycopg.errors.UniqueViolation:
                logger.debug(f"the other worker is processing the submission {submission_id}")
                return delivered_events_number, sequence_number, False

        return delivered_events_number, sequence_number, None
