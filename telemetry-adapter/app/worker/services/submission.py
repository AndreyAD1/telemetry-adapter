import logging

from app.worker.infrastructure.clients.exceptions import QueueClientException
from app.worker.infrastructure.clients.interfaces import QueueClient
from app.worker.infrastructure.event_streamer import (
    EventStreamer,
    EventStreamerException
)
from app.worker.services.exceptions import SubmissionReceivingError


logger = logging.getLogger(__file__)


class SubmissionService:
    def __init__(
            self,
            queue_client: QueueClient,
            event_streamer: EventStreamer
    ):
        self.queue_client = queue_client
        self.event_streamer = event_streamer

    def get_submissions(self):
        try:
            messages = self.queue_client.get_messages()
        except QueueClientException as ex:
            raise SubmissionReceivingError from ex

        valid_messages, invalid_messages = self.verify_submissions(messages)
        return valid_messages, invalid_messages

    @staticmethod
    def verify_submissions(submissions):
        return submissions, []

    async def process_invalid_submission(self, submission):
        logger.debug(f"process invalid submission: {submission}")
        self.queue_client.delete_message(submission["ReceiptHandle"])

    async def process_valid_submission(self, submission):
        logger.debug(f"process valid submission: {submission}")
        try:
            success = self.event_streamer.downstream_submission(submission)
        except EventStreamerException as ex:
            raise ex

        if success:
            self.queue_client.delete_message(submission["ReceiptHandle"])
