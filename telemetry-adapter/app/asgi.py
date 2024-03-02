import asyncio
from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI

from app.api.endpoints import router
from app.worker.worker import get_worker


# logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
# stream_handler = logging.StreamHandler(sys.stdout)
# log_formatter = logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
# stream_handler.setFormatter(log_formatter)
# logger.addHandler(stream_handler)


@asynccontextmanager
async def run_worker(application: FastAPI):
    # TODO a context manager
    worker = get_worker()
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker.run())
            worker.status = True
            yield
            worker.status = False
    finally:
        worker.status = False


app = FastAPI(title="Telemetry Adapter", version="1.0.0", lifespan=run_worker)
app.include_router(router, prefix="/v1")
