import logging
import traceback
from typing import Mapping, Any, Iterable

import boto3
import botocore.exceptions

from app.worker.infrastructure.clients.interfaces import QueueClient
from app.worker.infrastructure.clients.exceptions import (
    QueueClientReceivingException
)

logger = logging.getLogger(__file__)


class SQSClient(QueueClient):
    def __init__(self, queue_url, endpoint_url):
        self.sqs_client = boto3.client("sqs", endpoint_url=endpoint_url)
        self.queue_url = queue_url

    def get_messages(self) -> Iterable[Mapping[str, Any]]:
        logger.debug(f"get messages from {self.queue_url}")
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
        except botocore.exceptions.ClientError as ex:
            logger.warning(f"Error while retrieving messages: {self.queue_url}: {ex}")
            raise QueueClientReceivingException from ex

        messages = response.get("Messages", [])
        return messages

    def delete_message(self, receipt_handle: str):
        logger.debug(f"delete the message {receipt_handle}")
        try:
            self.sqs_client.delete_message(
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
        logger.debug(f"successful deletion: {receipt_handle}")
