import logging

from fastapi import FastAPI

from src.api.v1.api_router import api_v1_router
from src.core.config import config
from src.core.exceptions import add_exception_handlers
from src.utils.logging import setup_logging

log_level = getattr(config, "LOG_LEVEL", "INFO")
setup_logging(log_level=log_level)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(api_v1_router, prefix="/v1")

add_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}
