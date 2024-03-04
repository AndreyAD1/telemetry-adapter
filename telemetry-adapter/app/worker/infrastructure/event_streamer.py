from abc import ABC, abstractmethod
from datetime import datetime, UTC
import logging
from enum import Enum
from typing import Union
from uuid import uuid4

from psycopg.rows import class_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, UUID4, AwareDatetime, PositiveInt

from app.worker.infrastructure.clients.exceptions import KinesisClientException
from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient, PostgresPoolManager
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
    submission_id: UUID4
    status: StatusEnum
    number_of_delivered_events: PositiveInt


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
            # async with conn.cursor(row_factory=class_row(StoredSubmission)) as cur:
            async with conn.cursor() as cur:
                cur = await cur.execute("SELECT 1")
                # cur = await cur.execute(
                #     "SELECT * FROM submission WHERE id = %s",
                #     (submission.submission_id,)
                # )
                stored_submission = await cur.fetchone()
                if stored_submission:
                    logger.debug(f"query_result {stored_submission}")
                else:
                    # create a new pending submission
                    pass

        logger.debug(f"downstream a submission {submission}")

        events = []
        for event_type, event_details in all_events:
            event = KinesisEvent(
                id=uuid4(),
                event_type=event_type,
                device_id=submission.device_id,
                processing_timestamp=datetime.now(UTC),
                event_details=event_details
            )
            events.append(event)

        sequence_number = None
        for event in events:
            json_event = event.model_dump_json()
            try:
                sequence_number = await self.kinesis_client.put_record(
                    self.stream_name,
                    json_event.encode(),
                    str(event.device_id),
                    sequence_number
                )
            except KinesisClientException:
                return False

            logger.debug(f"receive a sequence number {sequence_number} for {json_event}")

        return True
