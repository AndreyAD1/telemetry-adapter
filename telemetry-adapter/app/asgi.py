import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager

import psycopg
import psycopg_pool
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from app.api.endpoints import router
from app.worker.infrastructure.clients.kinesis import KinesisClient
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

    sqs_client = SQSClient(
        settings.queue_url,
        settings.endpoint_url,
        settings.max_message_number_by_request,
        settings.sqs_visibility_timeout,
        settings.message_wait_time
    )
    async with AsyncConnectionPool(
            conninfo=settings.db_url,
            check=AsyncConnectionPool.check_connection,
            timeout=15
    ) as pg_pool:
        try:
            async with pg_pool.connection() as conn:
                logger.debug("check the DB connection")
                await conn.execute("SELECT 1")
        except psycopg.OperationalError:
            logger.error(f"No database connection: {settings.db_url}")
            raise

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
