import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.models.input import InputRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/input",
    tags=["input"],
)


@router.post(
    "",
    tags=["input"],
)
async def input(
    data: InputRequest,
) -> JSONResponse:
    """Input endpoint for processing input data.

    Args:
        data (InputRequest): InputRequest content
    Returns:
        JSONResponse: Object containing the data, status code, and error message.
    """
    log = logger.getChild("input")
    log.debug(f"Received data: {data}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": f"Hi there {data.name}",
            "status_code": status.HTTP_200_OK,
        },
    )
