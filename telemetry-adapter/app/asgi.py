import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from app.api.endpoints import router
from app.worker.infrastructure.clients.kinesis import KinesisClient
from app.worker.infrastructure.clients.postgres import PostgresClient
from app.worker.infrastructure.clients.sqs import SQSClient
from app.worker.infrastructure.event_streamer import KinesisStreamer
from app.worker.services.submission import TelemetryService
from app.worker.worker import Worker, register_worker
from app.settings import get_settings


logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    if settings.debug:
        logging.getLogger("app").setLevel(logging.DEBUG)

    # TODO a context manager
    sqs_client = SQSClient(
        settings.queue_url,
        settings.endpoint_url,
        settings.max_message_number_by_request,
        settings.sqs_visibility_timeout,
        settings.message_wait_time
    )
    async with AsyncConnectionPool(conninfo=settings.db_url) as pg_pool:
        kinesis_client = KinesisClient(settings.endpoint_url)
        kinesis_streamer = KinesisStreamer(kinesis_client, pg_pool)
        submission_service = TelemetryService(sqs_client, kinesis_streamer)
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
