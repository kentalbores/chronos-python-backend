import logging
from datetime import date

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse

from src.services.attendance import (
    get_today_attendance,
    get_attendance_by_date,
    get_employee_attendance,
    get_employee_distribution,
    get_attendance_report,
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
        
        # Convert to dict for JSON response
        response_data = {
            "date": str(attendance.response_date),
            "summary": {
                "total_employees": attendance.summary.total_employees,
                "present": attendance.summary.present,
                "absent": attendance.summary.absent,
                "early_in": attendance.summary.early_in,
                "on_time": attendance.summary.on_time,
                "late_entry": attendance.summary.late_entry,
            },
            "employees": [
                {
                    "user_id": emp.user_id,
                    "employee_name": emp.employee_name,
                    "department_name": emp.department_name,
                    "date": str(emp.attendance_date),
                    "clock_in": emp.clock_in.isoformat() if emp.clock_in else None,
                    "clock_out": emp.clock_out.isoformat() if emp.clock_out else None,
                    "total_hours": emp.total_hours,
                    "status": emp.status.value,
                    "tap_count": emp.tap_count,
                }
                for emp in attendance.employees
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
        
        response_data = {
            "date": str(attendance.response_date),
            "summary": {
                "total_employees": attendance.summary.total_employees,
                "present": attendance.summary.present,
                "absent": attendance.summary.absent,
                "early_in": attendance.summary.early_in,
                "on_time": attendance.summary.on_time,
                "late_entry": attendance.summary.late_entry,
            },
            "employees": [
                {
                    "user_id": emp.user_id,
                    "employee_name": emp.employee_name,
                    "department_name": emp.department_name,
                    "date": str(emp.attendance_date),
                    "clock_in": emp.clock_in.isoformat() if emp.clock_in else None,
                    "clock_out": emp.clock_out.isoformat() if emp.clock_out else None,
                    "total_hours": emp.total_hours,
                    "status": emp.status.value,
                    "tap_count": emp.tap_count,
                }
                for emp in attendance.employees
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
    description="Get today's attendance record for a specific employee.",
)
async def get_employee_today_attendance(user_id: str) -> JSONResponse:
    """Get today's attendance for a specific employee.

    Args:
        user_id: The employee's user UUID

    Returns:
        JSONResponse: Employee's attendance record.
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
        
        response_data = {
            "user_id": attendance.user_id,
            "employee_name": attendance.employee_name,
            "department_name": attendance.department_name,
            "date": str(attendance.attendance_date),
            "clock_in": attendance.clock_in.isoformat() if attendance.clock_in else None,
            "clock_out": attendance.clock_out.isoformat() if attendance.clock_out else None,
            "total_hours": attendance.total_hours,
            "status": attendance.status.value,
            "tap_count": attendance.tap_count,
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
    description="Get attendance record for a specific employee on a specific date.",
)
async def get_employee_attendance_by_date(user_id: str, target_date: date) -> JSONResponse:
    """Get attendance for a specific employee on a specific date.

    Args:
        user_id: The employee's user UUID
        target_date: The date to get attendance for (YYYY-MM-DD format)

    Returns:
        JSONResponse: Employee's attendance record.
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
        
        response_data = {
            "user_id": attendance.user_id,
            "employee_name": attendance.employee_name,
            "department_name": attendance.department_name,
            "date": str(attendance.attendance_date),
            "clock_in": attendance.clock_in.isoformat() if attendance.clock_in else None,
            "clock_out": attendance.clock_out.isoformat() if attendance.clock_out else None,
            "total_hours": attendance.total_hours,
            "status": attendance.status.value,
            "tap_count": attendance.tap_count,
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
        
        response_data = {
            "total_employees": distribution.total_employees,
            "present": distribution.present,
            "absent": distribution.absent,
            "distribution": [
                {
                    "department_name": dept.department_name,
                    "count": dept.count,
                    "color": dept.color,
                }
                for dept in distribution.distribution
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
        
        response_data = {
            "date": str(target_date),
            "total_employees": distribution.total_employees,
            "present": distribution.present,
            "absent": distribution.absent,
            "distribution": [
                {
                    "department_name": dept.department_name,
                    "count": dept.count,
                    "color": dept.color,
                }
                for dept in distribution.distribution
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )
    
    try:
        report = await get_attendance_report(start_date, end_date)
        log.debug(f"Generated report for {report.summary.total_employees} employees from {start_date} to {end_date}")
        
        response_data = {
            "summary": {
                "start_date": str(report.summary.start_date),
                "end_date": str(report.summary.end_date),
                "total_working_days": report.summary.total_working_days,
                "total_employees": report.summary.total_employees,
            },
            "employees": [
                {
                    "user_id": emp.user_id,
                    "employee_name": emp.employee_name,
                    "department_name": emp.department_name,
                    "presents": emp.presents,
                    "lates": emp.lates,
                    "absences": emp.absences,
                    "total_hours": emp.total_hours,
                    "total_attendance_score": emp.total_attendance_score,
                    "performance": emp.performance,
                }
                for emp in report.employees
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )
    except Exception as e:
        log.error(f"Error generating attendance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

