import logging

from app.infrastructure.clients.interfaces import QueueClient


logger = logging.getLogger(__file__)


class SQSClient(QueueClient):
    def __init__(self, queue_url):
        self.queue_url = queue_url

    def get_messages(self):
        logger.debug("get messages")

    def delete_message(self, id_):
        logger.debug("delete messages")
