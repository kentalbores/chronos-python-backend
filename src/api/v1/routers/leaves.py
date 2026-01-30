import logging
from typing import Optional, List
from datetime import date

from fastapi import APIRouter, status, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from src.models.leaves import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestFilter,
    LeaveRequestResponse
)
from src.services.leaves import (
    get_all_leaves,
    get_leave_by_id,
    create_leave_request,
    update_leave_request,
    delete_leave_request
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/leaves",
    tags=["leaves"],
)


@router.get(
    "",
    summary="Get all leave requests",
    description="Retrieve a list of leave requests. Can be filtered by user, status, type, and date range.",
    response_model=List[LeaveRequestResponse]
)
async def get_leaves(
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Approved, Pending, Rejected)"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by leave type"),
    date_from: Optional[date] = Query(None, description="Filter by start date (from)"),
    date_to: Optional[date] = Query(None, description="Filter by start date (to)"),
    limit: int = Query(100, ge=1, le=500, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> JSONResponse:
    """
    Get all leave requests.
    """
    log = logger.getChild("get_leaves")
    try:
        filters = LeaveRequestFilter(
            user_id=user_id,
            status=status_filter,
            type=type_filter,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        leaves = get_all_leaves(filters)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=leaves
        )
    except Exception as e:
        log.error(f"Error retrieving leave requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{leave_id}",
    summary="Get leave request by ID",
    description="Retrieve a specific leave request by ID.",
    response_model=LeaveRequestResponse
)
async def get_leave(leave_id: str) -> JSONResponse:
    """
    Get leave request by ID.
    """
    log = logger.getChild("get_leave")
    try:
        leave = get_leave_by_id(leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request {leave_id} not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=leave
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving leave request {leave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "",
    summary="Create a leave request",
    description="Submit a new leave request.",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_leave(leave_data: LeaveRequestCreate) -> JSONResponse:
    """
    Create a new leave request.
    """
    log = logger.getChild("create_leave")
    try:
        new_leave = create_leave_request(leave_data)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=new_leave
        )
    except Exception as e:
        log.error(f"Error creating leave request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch(
    "/{leave_id}",
    summary="Update leave request",
    description="Update a leave request's status or details.",
    response_model=LeaveRequestResponse
)
async def update_leave(
    leave_id: str,
    leave_data: LeaveRequestUpdate
) -> JSONResponse:
    """
    Update leave request.
    """
    log = logger.getChild("update_leave")
    try:
        updated_leave = update_leave_request(leave_id, leave_data)
        if not updated_leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request {leave_id} not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=updated_leave
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating leave request {leave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{leave_id}",
    summary="Delete leave request",
    description="Soft delete a leave request.",
    status_code=status.HTTP_200_OK
)
async def delete_leave(leave_id: str):
    """
    Soft delete leave request.
    """
    log = logger.getChild("delete_leave")
    try:
        success = delete_leave_request(leave_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request {leave_id} not found"
            )
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content={"message": "Leave request deleted"}
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting leave request {leave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
