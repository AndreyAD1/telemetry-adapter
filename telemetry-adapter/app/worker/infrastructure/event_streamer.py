from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import List

from pydantic import BaseModel, UUID4

from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient

logger = logging.getLogger(__file__)


class EventStreamerException(Exception):
    pass


class NewProcesses(BaseModel):
    cmdl: str
    user: str


class NetworkConnections(BaseModel):
    source_ip: str
    destination_ip: str
    destination_port: int


class Events(BaseModel):
    new_process: List[NewProcesses]
    network_connection: List[NetworkConnections]


class Submission(BaseModel):
    submission_id: UUID4
    device_id: UUID4
    time_created: datetime
    events: Events


class EventStreamer(ABC):
    @abstractmethod
    def downstream_submission(self, submission: Submission):
        pass


class KinesisStreamer(EventStreamer):
    def __init__(self, kinesis_client: KinesisClient, pg_client: PostgresClient):
        self.kinesis_client = kinesis_client
        self.pg_client = pg_client

    def downstream_submission(self, submission: Submission) -> bool:
        logger.debug(f"downstream a submission {submission}")
        return True
