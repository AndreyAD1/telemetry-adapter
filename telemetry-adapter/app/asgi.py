import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import router
from app.worker.worker import get_worker
from app.logger import configure_logger
from app.settings import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logger(get_settings().debug)
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


app = FastAPI(title="Telemetry Adapter", version="1.0.0", lifespan=lifespan)
app.include_router(router, prefix="/v1")
