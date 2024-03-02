import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import router
from app.worker.worker import Worker


@asynccontextmanager
async def run_worker(app: FastAPI):
    # TODO a context manager
    worker = Worker()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker.run())
        yield


app = FastAPI(title="Telemetry Adapter", version="1.0.0", lifespan=run_worker)
app.include_router(router, prefix="/v1")
