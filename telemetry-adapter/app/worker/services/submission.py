import logging
from typing import Tuple, List, Mapping, Any, Iterable

import pydantic
from pydantic import BaseModel

from app.worker.infrastructure.clients.exceptions import QueueClientException, QueueClientUnexpectedMessage
from app.worker.infrastructure.clients.interfaces import QueueClient
from app.worker.infrastructure.event_streamer import (
    EventStreamer,
    EventStreamerException, Submission
)
from app.worker.services.exceptions import SubmissionReceivingError


logger = logging.getLogger(__file__)


class Message(BaseModel):
    deletion_id: str
    submission: Submission = None


class TelemetryService:
    def __init__(
        self,
        queue_client: QueueClient,
        event_streamer: EventStreamer
    ):
        self.queue_client = queue_client
        self.event_streamer = event_streamer

    def get_messages(self) -> Tuple[List[Message], List[Message]]:
        try:
            messages = self.queue_client.get_messages()
        except QueueClientException as ex:
            raise SubmissionReceivingError from ex

        valid_submissions, invalid_submissions = self.parse_messages(messages)
        return valid_submissions, invalid_submissions

    def parse_messages(self, messages: Iterable[Mapping[str, Any]]) -> Tuple[List[Message], List[Message]]:
        valid_messages, invalid_messages = [], []
        for message in messages:
            deletion_id = self.queue_client.get_deletion_id(message)
            try:
                parsed_message = Message(deletion_id=deletion_id)
            except pydantic.ValidationError as ex:
                logger.error(f"The unexpected deletion id: {ex}. Message: {message}")
                continue

            try:
                raw_submission = self.queue_client.get_submission_from_message(
                    message
                )
            except QueueClientUnexpectedMessage:
                invalid_messages.append(parsed_message)
                continue

            try:
                submission = Submission(**raw_submission)
            except pydantic.ValidationError as ex:
                logger.warning(
                    f"can not retrieve a submission from the message: {ex}. "
                    f"Message: {message}"
                )
                invalid_messages.append(parsed_message)
                continue

            parsed_message.submission = submission
            valid_messages.append(parsed_message)

        return valid_messages, invalid_messages

    async def process_invalid_message(self, message: Message):
        logger.debug(f"process invalid submission: {message}")
        self.queue_client.delete_message(message.deletion_id)

    async def process_valid_message(self, message: Message):
        logger.debug(f"process valid message: {message}")
        try:
            success = self.event_streamer.downstream_submission(message.submission)
        except EventStreamerException as ex:
            raise ex

        if success:
            self.queue_client.delete_message(message.deletion_id)
