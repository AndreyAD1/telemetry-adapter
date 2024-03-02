import asyncio
import logging

from app.infrastructure.clients.interfaces import QueueClient

logger = logging.getLogger(__file__)


class Worker:
    def __init__(self, queue_client: QueueClient):
        self.status = False
        self.queue_client = queue_client

    async def run(self):
        self.status = True
        while self.status:
            logger.debug(f"Worker is on the run. Status: {self.status}")
            messages = self.queue_client.get_messages()
            logger.debug(f"Received messages: {messages}")
            await asyncio.sleep(2)


worker = None


def register_worker(new_worker: Worker):
    global worker
    worker = new_worker


def get_worker():
    return worker
