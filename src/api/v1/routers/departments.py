import logging

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse

from src.models.departments import DepartmentCreate, DepartmentUpdate, DepartmentDeleteRequest
from src.services.departments import (
    get_all_departments,
    get_department_by_id,
    create_department,
    update_department,
    delete_department,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
)


@router.get(
    "",
    tags=["departments"],
    summary="Get all departments",
    description="Retrieve a list of all departments in the system.",
)
async def get_departments() -> JSONResponse:
    """Get all departments endpoint.

    Returns:
        JSONResponse: List of all departments.
    """
    log = logger.getChild("get_departments")
    try:
        departments = get_all_departments()
        log.debug(f"Retrieved {len(departments)} departments")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Departments retrieved successfully",
                "data": departments,
            },
        )
    except Exception as e:
        log.error(f"Error retrieving departments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{dep_id}",
    tags=["departments"],
    summary="Get department by ID",
    description="Retrieve a specific department by its ID.",
)
async def get_department(dep_id: int) -> JSONResponse:
    """Get department by ID endpoint.

    Args:
        dep_id: The ID of the department to retrieve.

    Returns:
        JSONResponse: Department data.
    """
    log = logger.getChild("get_department")
    try:
        department = get_department_by_id(dep_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {dep_id} not found",
            )
        log.debug(f"Retrieved department: {dep_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Department retrieved successfully",
                "data": department,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving department {dep_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "",
    tags=["departments"],
    summary="Create a new department",
    description="Create a new department.",
)
async def create_new_department(department_data: DepartmentCreate) -> JSONResponse:
    """Create department endpoint.

    Args:
        department_data: The department data to create.

    Returns:
        JSONResponse: Created department data.
    """
    log = logger.getChild("create_department")
    try:
        new_department = create_department(department_data)
        log.info(f"Created new department: {new_department.get('dep_id')}")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Department created successfully",
                "data": new_department,
            },
        )
    except Exception as e:
        log.error(f"Error creating department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch(
    "",
    tags=["departments"],
    summary="Update a department",
    description="Update an existing department's details.",
)
async def update_existing_department(department_data: DepartmentUpdate) -> JSONResponse:
    """Update department endpoint.

    Args:
        department_data: The department data to update (includes dep_id).

    Returns:
        JSONResponse: Updated department data.
    """
    log = logger.getChild("update_department")
    try:
        updated_department = update_department(department_data)
        if not updated_department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_data.dep_id} not found",
            )
        log.info(f"Updated department: {department_data.dep_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Department updated successfully",
                "data": updated_department,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating department {department_data.dep_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "",
    tags=["departments"],
    summary="Delete a department",
    description="Delete a department by providing its ID in the request body.",
)
async def delete_existing_department(request: DepartmentDeleteRequest) -> JSONResponse:
    """Delete department endpoint.

    Args:
        request: Request body containing the dep_id to delete.

    Returns:
        JSONResponse: Confirmation of deletion.
    """
    log = logger.getChild("delete_department")
    try:
        deleted_department = delete_department(request.dep_id)
        if not deleted_department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {request.dep_id} not found",
            )
        log.info(f"Deleted department: {request.dep_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Department deleted successfully",
                "data": deleted_department,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting department {request.dep_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

