from abc import ABC, abstractmethod
import logging

from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient
from app.worker.infrastructure.types import Submission

logger = logging.getLogger(__file__)


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
