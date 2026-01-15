import logging
from datetime import date

from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import JSONResponse

from src.services.attendance import (
    get_today_attendance,
    get_attendance_by_date,
    get_employee_attendance,
    get_employee_distribution,
    get_attendance_report,
    get_employee_attendance_period,
    get_employee_attendance_range,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
)


@router.get(
    "/today",
    tags=["attendance"],
    summary="Get today's attendance",
    description="Get attendance records for all employees for today.",
)
async def get_todays_attendance() -> JSONResponse:
    """Get today's attendance for all employees.

    Returns:
        JSONResponse: Daily attendance with summary and employee records.
    """
    log = logger.getChild("get_todays_attendance")
    try:
        attendance = await get_today_attendance()
        log.debug(f"Retrieved attendance for {attendance.summary.total_employees} employees")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(
                mode='json',
                by_alias=True,
                exclude={'employees': {'__all__': {'logs'}}}
            ),
        )
    except Exception as e:
        log.error(f"Error getting today's attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/date/{target_date}",
    tags=["attendance"],
    summary="Get attendance by date",
    description="Get attendance records for all employees for a specific date.",
)
async def get_attendance_for_date(target_date: date) -> JSONResponse:
    """Get attendance for all employees on a specific date.

    Args:
        target_date: The date to get attendance for (YYYY-MM-DD format)

    Returns:
        JSONResponse: Daily attendance with summary and employee records.
    """
    log = logger.getChild("get_attendance_for_date")
    try:
        attendance = await get_attendance_by_date(target_date)
        log.debug(f"Retrieved attendance for {attendance.summary.total_employees} employees on {target_date}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(
                mode='json',
                by_alias=True,
                exclude={'employees': {'__all__': {'logs'}}}
            ),
        )
    except Exception as e:
        log.error(f"Error getting attendance for {target_date}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/employee/{user_id}",
    tags=["attendance"],
    summary="Get employee's today attendance",
    description="Get today's attendance record for a specific employee, including all tap-in/tap-out logs.",
)
async def get_employee_today_attendance(user_id: str) -> JSONResponse:
    """Get today's attendance for a specific employee.

    Args:
        user_id: The employee's user UUID

    Returns:
        JSONResponse: Employee's attendance record with all tap logs.
    """
    log = logger.getChild("get_employee_today_attendance")
    try:
        attendance = await get_employee_attendance(user_id)
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {user_id} not found",
            )
        
        log.debug(f"Retrieved attendance for employee {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(mode='json', by_alias=True),
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting attendance for employee {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/employee/{user_id}/date/{target_date}",
    tags=["attendance"],
    summary="Get employee's attendance by date",
    description="Get attendance record for a specific employee on a specific date, including all tap-in/tap-out logs.",
)
async def get_employee_attendance_by_date(user_id: str, target_date: date) -> JSONResponse:
    """Get attendance for a specific employee on a specific date.

    Args:
        user_id: The employee's user UUID
        target_date: The date to get attendance for (YYYY-MM-DD format)

    Returns:
        JSONResponse: Employee's attendance record with all tap logs.
    """
    log = logger.getChild("get_employee_attendance_by_date")
    try:
        attendance = await get_employee_attendance(user_id, target_date)
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {user_id} not found",
            )
        
        log.debug(f"Retrieved attendance for employee {user_id} on {target_date}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(mode='json', by_alias=True),
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting attendance for employee {user_id} on {target_date}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/distribution",
    tags=["attendance"],
    summary="Get employee distribution for pie chart",
    description="Get today's employee distribution by department for pie chart visualization.",
)
async def get_distribution_today() -> JSONResponse:
    """Get employee distribution by department for today.

    Returns data suitable for a pie chart showing:
    - Present employees grouped by department
    - Absent employees count

    Returns:
        JSONResponse: Distribution data for pie chart.
    """
    log = logger.getChild("get_distribution_today")
    try:
        distribution = await get_employee_distribution()
        log.debug(f"Retrieved distribution: {distribution.present}/{distribution.total_employees} present")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=distribution.model_dump(mode='json'),
        )
    except Exception as e:
        log.error(f"Error getting employee distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/distribution/date/{target_date}",
    tags=["attendance"],
    summary="Get employee distribution by date",
    description="Get employee distribution by department for a specific date.",
)
async def get_distribution_by_date(target_date: date) -> JSONResponse:
    """Get employee distribution by department for a specific date.

    Args:
        target_date: The date to get distribution for (YYYY-MM-DD format)

    Returns:
        JSONResponse: Distribution data for pie chart.
    """
    log = logger.getChild("get_distribution_by_date")
    try:
        distribution = await get_employee_distribution(target_date)
        log.debug(f"Retrieved distribution for {target_date}: {distribution.present}/{distribution.total_employees} present")
        response = distribution.model_dump(mode='json')
        response["date"] = str(target_date)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response,
        )
    except Exception as e:
        log.error(f"Error getting employee distribution for {target_date}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/report",
    tags=["attendance"],
    summary="Get attendance report for a date range",
    description="Get aggregated attendance report for all employees over a specified date range. Returns presents, lates, absences, and total_hours for each employee.",
)
async def get_report(start_date: date, end_date: date) -> JSONResponse:
    """Get attendance report for all employees over a date range.

    Args:
        start_date: Start date of the report (YYYY-MM-DD format, inclusive)
        end_date: End date of the report (YYYY-MM-DD format, inclusive)

    Returns:
        JSONResponse: Attendance report with aggregated data per employee.
    
    Example:
        GET /attendance/report?start_date=2025-12-19&end_date=2025-12-30
    """
    log = logger.getChild("get_report")
    
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )
    
    try:
        report = await get_attendance_report(start_date, end_date)
        log.debug(f"Generated report for {report.summary.total_employees} employees from {start_date} to {end_date}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=report.model_dump(mode='json'),
        )
    except Exception as e:
        log.error(f"Error generating attendance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/employee/{user_id}/period",
    tags=["attendance"],
    summary="Get employee's attendance for this week or month",
    description="Get attendance records for a specific employee for the current week or month.",
)
async def get_employee_period_attendance(
    user_id: str,
    period: str = Query(..., description="Period to get: 'week' for this week, 'month' for this month", regex="^(week|month)$"),
) -> JSONResponse:
    """Get attendance for a specific employee over a period.

    Args:
        user_id: The employee's user UUID
        period: 'week' for this week, 'month' for this month

    Returns:
        JSONResponse: Employee's attendance data for the period.
    """
    log = logger.getChild("get_employee_period_attendance")
    try:
        attendance = await get_employee_attendance_period(user_id, period)
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {user_id} not found",
            )
        
        log.debug(f"Retrieved {period} attendance for employee {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(mode='json'),
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting {period} attendance for employee {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/employee/{user_id}/range",
    tags=["attendance"],
    summary="Get employee's attendance for a date range",
    description="Get attendance records for a specific employee over a custom date range.",
)
async def get_employee_range_attendance(
    user_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD format, inclusive)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD format, inclusive)"),
) -> JSONResponse:
    """Get attendance for a specific employee over a date range.

    Args:
        user_id: The employee's user UUID
        start_date: Start date of the range (inclusive)
        end_date: End date of the range (inclusive)

    Returns:
        JSONResponse: Employee's attendance data for the date range.
    """
    log = logger.getChild("get_employee_range_attendance")
    
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )
    
    try:
        attendance = await get_employee_attendance_range(user_id, start_date, end_date)
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {user_id} not found",
            )
        
        log.debug(f"Retrieved attendance for employee {user_id} from {start_date} to {end_date}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=attendance.model_dump(mode='json'),
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting attendance for employee {user_id} from {start_date} to {end_date}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

