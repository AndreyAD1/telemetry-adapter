import logging

from fastapi import APIRouter


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/ping")
def ping() -> str:
    return "OK"
