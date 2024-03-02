import asyncio
import logging


logger = logging.getLogger(__name__)


class Worker:
    async def run(self):
        while True:
            logger.info("Worker is on the run log")
            print("Worker is on the run")
            await asyncio.sleep(2)
