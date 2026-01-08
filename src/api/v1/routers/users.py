import logging
from typing import Optional
from datetime import date

from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import JSONResponse

from src.models.users import UserCreate, UserUpdate, UserDeleteRequest, UserFilter, UserLoginInfoResponse
from src.services.users import (
    get_all_users,
    get_user_by_id,
    create_user,
    update_user,
    soft_delete_user,
    restore_user,
    get_user_login_info,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    tags=["users"],
    summary="Get all users",
    description="Retrieve a list of all users with optional filtering and search.",
)
async def get_users(
    search: Optional[str] = Query(None, description="Search by name or email (partial match)"),
    dep_name: Optional[str] = Query(None, description="Filter by department name"),
    work_status: Optional[str] = Query(None, description="Filter by work status (on_site, wfh)"),
    shift_type: Optional[str] = Query(None, description="Filter by shift type (day, night)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (Intern, Regular)"),
    has_rfid: Optional[bool] = Query(None, description="Filter by RFID status"),
    date_hired_from: Optional[date] = Query(None, description="Filter by hire date (from)"),
    date_hired_to: Optional[date] = Query(None, description="Filter by hire date (to)"),
    limit: int = Query(100, ge=1, le=500, description="Max number of results (1-500)"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> JSONResponse:
    """Get all users endpoint with filtering and search.

    Returns:
        JSONResponse: Array of all users matching the filter criteria.
    """
    log = logger.getChild("get_users")
    try:
        # Build filter object
        filters = UserFilter(
            search=search,
            dep_name=dep_name,
            work_status=work_status,
            shift_type=shift_type,
            employment_type=employment_type,
            has_rfid=has_rfid,
            date_hired_from=date_hired_from,
            date_hired_to=date_hired_to,
            limit=limit,
            offset=offset,
        )
        
        users = get_all_users(filters)
        log.debug(f"Retrieved {len(users)} users")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=users,  # Return array directly
        )
    except Exception as e:
        log.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{user_id}",
    tags=["users"],
    summary="Get user by ID",
    description="Retrieve a specific user by their ID with employee details.",
)
async def get_user(user_id: str) -> JSONResponse:
    """Get user by ID endpoint.

    Args:
        user_id: The ID of the user to retrieve.

    Returns:
        JSONResponse: User data with employee details.
    """
    log = logger.getChild("get_user")
    try:
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        log.debug(f"Retrieved user: {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "",
    tags=["users"],
    summary="Create a new user",
    description="Create a new user in Auth0 and database with employee details.",
)
async def create_new_user(user_data: UserCreate) -> JSONResponse:
    """Create user endpoint.

    Creates user in Auth0 first, then in Supabase.

    Args:
        user_data: The user data to create (includes email and password for Auth0).

    Returns:
        JSONResponse: Created user data.
    """
    log = logger.getChild("create_user")
    try:
        new_user = await create_user(user_data)
        log.info(f"Created new user: {new_user.get('user_id')}")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=new_user,
        )
    except Exception as e:
        log.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch(
    "/{user_id}",
    tags=["users"],
    summary="Update a user",
    description="Update an existing user's details.",
)
async def update_existing_user(user_id: str, user_data: UserUpdate) -> JSONResponse:
    """Update user endpoint.

    Args:
        user_id: The ID of the user to update.
        user_data: The user data to update.

    Returns:
        JSONResponse: Updated user data.
    """
    log = logger.getChild("update_user")
    try:
        updated_user = update_user(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        log.info(f"Updated user: {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=updated_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "",
    tags=["users"],
    summary="Soft delete a user",
    description="Soft delete a user by setting deleted_at and blocking Auth0 login (canLogin: false).",
)
async def delete_existing_user(request: UserDeleteRequest) -> JSONResponse:
    """Soft delete user endpoint.

    Sets deleted_at in database and canLogin: false in Auth0.
    Does NOT permanently delete the user.

    Args:
        request: Request body containing the user_id to delete.

    Returns:
        JSONResponse: Confirmation of soft deletion.
    """
    log = logger.getChild("delete_user")
    try:
        deleted_user = await soft_delete_user(request.user_id)
        if not deleted_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {request.user_id} not found",
            )
        log.info(f"Soft deleted user: {request.user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User soft deleted successfully",
                "user_id": request.user_id,
                "deleted_at": deleted_user.get("deleted_at"),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error soft deleting user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{user_id}/restore",
    tags=["users"],
    summary="Restore a soft-deleted user",
    description="Restore a soft-deleted user by clearing deleted_at and enabling Auth0 login.",
)
async def restore_deleted_user(user_id: str) -> JSONResponse:
    """Restore soft-deleted user endpoint.

    Clears deleted_at in database and sets canLogin: true in Auth0.

    Args:
        user_id: The ID of the user to restore.

    Returns:
        JSONResponse: Restored user data.
    """
    log = logger.getChild("restore_user")
    try:
        restored_user = await restore_user(user_id)
        if not restored_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        log.info(f"Restored user: {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=restored_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error restoring user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/auth0/{auth0_id:path}",
    tags=["users"],
    summary="Get user login info by Auth0 ID",
    description="Fetch user login info from Auth0 by auth0_id. Checks canLogin status, retrieves user roles, and determines first login status.",
    response_model=UserLoginInfoResponse,
)
async def get_user_by_auth0_id(auth0_id: str) -> JSONResponse:
    """Get user login info by Auth0 ID endpoint.

    This endpoint:
    1. Fetches user data from Auth0 using the auth0_id
    2. Checks if canLogin is true in app_metadata
    3. Gets user roles from Supabase
    4. Determines firstLogin status based on last_password_reset and last_login
    5. Returns user info with firstLogin, role, first_name, last_name, email, profile_url

    Args:
        auth0_id: The Auth0 user ID (e.g., 'auth0|695b775cb1168edd9248bad6')

    Returns:
        JSONResponse: User login info with firstLogin, role, first_name, last_name, email, profile_url
    """
    log = logger.getChild("get_user_by_auth0_id")
    try:
        user_info = await get_user_login_info(auth0_id)
        log.debug(f"Retrieved login info for auth0_id: {auth0_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user_info,
        )
    except Exception as e:
        error_msg = str(e)
        log.error(f"Error retrieving user by auth0_id {auth0_id}: {error_msg}")
        
        # Check for specific error conditions
        if "not allowed to login" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not allowed to login",
            )
        elif "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with auth0_id {auth0_id} not found",
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )
