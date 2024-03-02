from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI

from app.api.endpoints import router


app = FastAPI(title="HackerNews Title API", version="1.0.0")
app.include_router(router, prefix="/v1")
