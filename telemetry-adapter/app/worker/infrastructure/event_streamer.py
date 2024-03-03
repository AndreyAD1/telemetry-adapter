from abc import ABC, abstractmethod
from datetime import datetime, UTC
import logging
from typing import Union
from uuid import uuid4

from pydantic import BaseModel, UUID4, AwareDatetime

from app.worker.infrastructure.clients.exceptions import KinesisClientException
from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient
from app.worker.infrastructure.types import Submission, NewProcess, NetworkConnection

logger = logging.getLogger(__file__)


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


class KinesisStreamer(EventStreamer):
    def __init__(self, kinesis_client: KinesisClient, pg_client: PostgresClient):
        self.kinesis_client = kinesis_client
        self.pg_client = pg_client

    def downstream_submission(self, submission: Submission) -> bool:
        logger.debug(f"downstream a submission {submission}")
        new_processes = [("new_process", p) for p in submission.events.new_process]
        connections = [("network_connection", p) for p in submission.events.network_connection]
        all_events = new_processes + connections
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

        sequence_number = 0
        for event in events:
            try:
                sequence_number = self.kinesis_client.put_record(
                    event.model_dump_json(),
                    event.device_id,
                    sequence_number
                )
            except KinesisClientException:
                return False

        return True
