import asyncio
import logging
import traceback

from app.worker.services.exceptions import SubmissionReceivingError
from app.worker.services.submission import TelemetryService

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, submission_service: TelemetryService):
        self.status = False
        self.error_timeout = 2
        self.submission_service = submission_service

    async def run(self):
        self.status = True
        while self.status:
            logger.debug(f"Worker is on the run. Status: {self.status}")
            try:
                valid, invalid = self.submission_service.get_messages()
                logger.debug(f"Received valid submissions: {valid}")
                logger.debug(f'Received invalid submissions: {invalid}')
            except SubmissionReceivingError:
                logger.debug("can not receive submissions")
                await asyncio.sleep(self.error_timeout)
                continue

            awaitables = [
                *[self.submission_service.process_invalid_message(s) for s in invalid],
                *[self.submission_service.process_valid_message(s) for s in valid]
            ]
            results = await asyncio.gather(*awaitables, return_exceptions=True)
            for result in results:
                if not isinstance(result, Exception):
                    continue
                exc_trace = "".join(traceback.format_tb(result.__traceback__))
                logger.warning(f"a submission processing error: {exc_trace}: {result}")

            await asyncio.sleep(self.error_timeout)


worker = None


def register_worker(new_worker: Worker):
    global worker
    worker = new_worker


def get_worker():
    return worker
