from typing import Annotated

from fastapi import Depends, APIRouter

from app.worker.worker import Worker, get_worker


router = APIRouter()


@router.get("/healthcheck")
def ping(worker: Annotated[Worker, Depends(get_worker)]) -> dict:
    return {"worker_status": "OK" if worker.status else "Fail"}
