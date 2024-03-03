import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import router
from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient
from app.worker.infrastructure.clients.sqs import SQSClient

from app.worker.infrastructure.event_streamer import KinesisStreamer
from app.worker.services.submission import SubmissionService
from app.worker.worker import Worker, register_worker
from app.logger import configure_logger
from app.settings import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    configure_logger(settings.debug)
    # TODO a context manager
    sqs_client = SQSClient(settings.queue_url, settings.endpoint_url)
    pg_client = PostgresClient(settings.db_url)
    kinesis_client = KinesisClient(settings.kinesis_url)
    kinesis_streamer = KinesisStreamer(kinesis_client, pg_client)
    submission_service = SubmissionService(sqs_client, kinesis_streamer)
    worker = Worker(submission_service)
    register_worker(worker)
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
