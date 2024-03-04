import base64
import hashlib
import json
import logging
import traceback
from typing import Mapping, Any, Iterable

import boto3
import botocore.exceptions

from app.worker.infrastructure.clients.interfaces import QueueClient
from app.worker.infrastructure.clients.exceptions import (
    QueueClientReceivingException, QueueClientUnexpectedMessage
)
from app.worker.infrastructure.clients.session_manager import AWSSessionManager

logger = logging.getLogger(__name__)


class SQSClient(QueueClient):
    def __init__(
            self,
            queue_url,
            endpoint_url,
            max_message_number,
            visibility_timeout,
            wait_time
    ):
        self.sqs_client = boto3.client("sqs", endpoint_url=endpoint_url)
        self.endpoint_url = endpoint_url
        self.queue_url = queue_url
        self.max_message_number = max_message_number
        self.visibility_timeout = visibility_timeout
        self.wait_time = wait_time

    def _get_async_client(self):
        return AWSSessionManager("sqs", endpoint_url=self.endpoint_url)

    def get_messages(self) -> Iterable[Mapping[str, Any]]:
        logger.debug(f"get messages from {self.queue_url}")
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=['All'],
                MaxNumberOfMessages=self.max_message_number,
                VisibilityTimeout=self.visibility_timeout,
                WaitTimeSeconds=self.wait_time
            )
        except botocore.exceptions.ClientError as ex:
            logger.warning(f"Error while retrieving messages: {self.queue_url}: {ex}")
            raise QueueClientReceivingException from ex

        messages = response.get("Messages", [])
        return messages

    async def delete_message(self, receipt_handle: str):
        logger.debug(f"delete the message {receipt_handle}")
        async with self._get_async_client() as client:
            try:
                await client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            except botocore.exceptions.ClientError as ex:
                err = f"Error while deleting the message {receipt_handle}: {self.queue_url}: {ex}"
                logger.warning(err)
                raise QueueClientReceivingException from ex
            except Exception as ex:
                logger.warning(f"a deletion error {ex}: {traceback.format_exc()}")
                raise ex
            logger.debug(f"the successful deletion: {receipt_handle}")

    def get_deletion_id(self, message: Mapping[str, Any]) -> str:
        return message["ReceiptHandle"]

    def get_submission_from_message(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        body = message.get("Body")
        received_body_hash = message.get("MD5OfBody")
        if body is None or received_body_hash is None:
            err_msg = f"No body or no body hash is in the message {message}"
            logger.warning(err_msg)
            raise QueueClientUnexpectedMessage(msg=err_msg)

        calculated_body_hash = hashlib.md5(str.encode(body)).hexdigest()
        if received_body_hash != calculated_body_hash:
            err_msg = (
                f"The invalid body hash: {received_body_hash}. "
                f"Expect: {calculated_body_hash}. Message: {message}"
            )
            logger.warning(err_msg)
            raise QueueClientUnexpectedMessage(msg=err_msg)

        decoded_body = base64.standard_b64decode(body)
        submission = json.loads(decoded_body)
        logger.debug(f"the decoded message body: {decoded_body}")
        return submission
