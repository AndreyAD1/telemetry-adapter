import logging

import boto3
import botocore.exceptions

from app.infrastructure.clients.interfaces import QueueClient
from app.infrastructure.clients.exceptions import QueueClientException


logger = logging.getLogger(__file__)


class SQSClient(QueueClient):
    def __init__(self, queue_url, endpoint_url):
        self.sqs_client = boto3.client("sqs", endpoint_url=endpoint_url)
        self.queue_url = queue_url

    def get_messages(self):
        logger.debug(f"get messages from {self.queue_url}")
        try:
            messages = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
        except botocore.exceptions.ClientError as ex:
            logger.warning(f"Error while retrieving messages: {self.queue_url}: {ex}")
            raise QueueClientException from ex

        return messages

    def delete_message(self, id_):
        logger.debug("delete messages")
