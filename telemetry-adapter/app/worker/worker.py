import asyncio
import logging

from app.worker.infrastructure.clients.exceptions import QueueClientException
from app.worker.services.exceptions import SubmissionReceivingError
from app.worker.services.submission import SubmissionService

logger = logging.getLogger(__file__)


class Worker:
    def __init__(self, submission_service: SubmissionService):
        self.status = False
        self.submission_service = submission_service

    async def run(self):
        self.status = True
        while self.status:
            logger.debug(f"Worker is on the run. Status: {self.status}")
            try:
                valid, invalid = self.submission_service.get_submissions()
                logger.debug(f"Received valid submissions: {valid}")
                logger.debug(f'Received invalid submissions: {invalid}')
            except SubmissionReceivingError:
                logger.debug("can not receive submissions")



            await asyncio.sleep(2)


worker = None


def register_worker(new_worker: Worker):
    global worker
    worker = new_worker


def get_worker():
    return worker
