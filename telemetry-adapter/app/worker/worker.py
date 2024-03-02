import asyncio
from functools import cache


class Worker:
    def __init__(self):
        self.status = False

    async def run(self):
        self.status = True
        while True:
            print(f"Worker is on the run. Status: {self.status}")
            await asyncio.sleep(2)


@cache
def get_worker():
    return Worker()
