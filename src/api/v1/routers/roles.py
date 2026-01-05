import logging

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse

from src.services.roles import get_all_roles

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)


@router.get(
    "",
    tags=["roles"],
    summary="Get all roles",
    description="Retrieve a list of all roles except admin.",
)
async def get_roles() -> JSONResponse:
    """Get all roles endpoint.

    Returns:
        JSONResponse: Array of all roles excluding admin.
    """
    log = logger.getChild("get_roles")
    try:
        roles = get_all_roles()
        log.debug(f"Retrieved {len(roles)} roles")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=roles,
        )
    except Exception as e:
        log.error(f"Error retrieving roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

