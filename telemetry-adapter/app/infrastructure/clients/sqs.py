import logging

import boto3

from app.infrastructure.clients.interfaces import QueueClient


logger = logging.getLogger(__file__)


class SQSClient(QueueClient):
    def __init__(self, queue_url):
        self.sqs_client = boto3.client("sqs", endpoint_url="http://localstack:4566")
        self.queue_url = queue_url

    def get_messages(self):
        logger.debug(f"get messages from {self.queue_url}")
        messages = self.sqs_client.receive_message(
            QueueUrl=self.queue_url,
            AttributeNames=['All']
        )
        return messages

    def delete_message(self, id_):
        logger.debug("delete messages")
