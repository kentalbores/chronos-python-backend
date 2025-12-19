"""
Attendance Service

Combines OpenSearch attendance logs with Supabase employee data.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, time, timedelta, timezone

from src.services.opensearch import opensearch_client
from src.services.supabase import supabase_client
from src.models.attendance import (
    AttendanceStatus,
    EmployeeAttendance,
    AttendanceSummary,
    DailyAttendanceResponse,
    DepartmentDistribution,
    EmployeeDistributionResponse,
)

logger = logging.getLogger(__name__)

# Time thresholds for status determination
EARLY_IN_THRESHOLD = time(9, 0, 0)    # Before 9:00 AM = early-in
ON_TIME_THRESHOLD = time(9, 30, 0)     # Before 9:30 AM = on-time
# After 9:30 AM = late-entry


def _determine_status(clock_in_time: Optional[datetime]) -> AttendanceStatus:
    """
    Determine attendance status based on clock-in time.
    
    Rules:
    - Clock in before 9:00 AM = early-in
    - Clock in before 9:30 AM = on-time  
    - Clock in after 9:30 AM = late-entry
    - No clock-in = absent
    """
    if clock_in_time is None:
        return AttendanceStatus.ABSENT
    
    clock_in_local = clock_in_time.time()
    
    if clock_in_local < EARLY_IN_THRESHOLD:
        return AttendanceStatus.EARLY_IN
    elif clock_in_local < ON_TIME_THRESHOLD:
        return AttendanceStatus.ON_TIME
    else:
        return AttendanceStatus.LATE_ENTRY


def _calculate_total_hours(logs: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate total hours worked from attendance logs.
    
    Pairs tap-in/tap-out events and sums the durations.
    """
    if not logs:
        return None
    
    total_seconds = 0
    current_tap_in = None
    
    for log in logs:
        event_type = log.get('event_type')
        timestamp_str = log.get('timestamp')
        
        if not timestamp_str:
            continue
        
        # Parse timestamp
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
            else:
                timestamp = timestamp_str
        except ValueError:
            continue
        
        if event_type == 'tap-in':
            current_tap_in = timestamp
        elif event_type == 'tap-out' and current_tap_in:
            duration = (timestamp - current_tap_in).total_seconds()
            total_seconds += duration
            current_tap_in = None
    
    # If still clocked in, calculate time until now
    if current_tap_in:
        # Use current local time for comparison
        now = datetime.now()
        duration = (now - current_tap_in).total_seconds()
        # Ensure non-negative duration
        total_seconds += max(0, duration)
    
    # Convert to hours with 2 decimal places, return 0 if just clocked in
    return round(total_seconds / 3600, 2)


def _get_first_clock_in(logs: List[Dict[str, Any]]) -> Optional[datetime]:
    """Get the first tap-in timestamp from logs."""
    for log in logs:
        if log.get('event_type') == 'tap-in':
            timestamp_str = log.get('timestamp')
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        return datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                    return timestamp_str
                except ValueError:
                    continue
    return None


def _get_last_clock_out(logs: List[Dict[str, Any]]) -> Optional[datetime]:
    """
    Get the last tap-out timestamp from logs.
    Only returns a value if the LAST event is a tap-out (employee has left).
    If the last event is a tap-in (employee is working), returns None.
    """
    if not logs:
        return None
    
    # Check the last event - if it's a tap-in, employee is still working
    last_log = logs[-1]  # logs are sorted by timestamp ASC
    if last_log.get('event_type') == 'tap-in':
        return None  # Employee is currently clocked in
    
    # Last event is tap-out, find the last tap-out timestamp
    last_out = None
    for log in logs:
        if log.get('event_type') == 'tap-out':
            timestamp_str = log.get('timestamp')
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        last_out = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                    else:
                        last_out = timestamp_str
                except ValueError:
                    continue
    return last_out


async def get_today_attendance() -> DailyAttendanceResponse:
    """
    Get today's attendance for all employees.
    
    Returns:
        DailyAttendanceResponse with all employees and their attendance status
    """
    today = date.today()
    return await get_attendance_by_date(today)


async def get_attendance_by_date(target_date: date) -> DailyAttendanceResponse:
    """
    Get attendance for all employees on a specific date.
    
    Args:
        target_date: The date to get attendance for
    
    Returns:
        DailyAttendanceResponse with all employees and their attendance status
    """
    try:
        # Step 1: Get all active employees from Supabase with their RFID values
        employees_response = supabase_client.table('employees').select('*').execute()
        employees = employees_response.data
        
        # Get all active users
        users_response = supabase_client.table('users').select('*').is_('deleted_at', 'null').execute()
        users = {user['user_id']: user for user in users_response.data}
        
        # Get all departments
        departments_response = supabase_client.table('departments').select('*').execute()
        departments = {dep['dep_id']: dep for dep in departments_response.data}
        
        # Step 2: Get attendance logs from OpenSearch for target date
        attendance_logs = await opensearch_client.get_attendance_logs(target_date)
        
        # Group logs by card_id
        logs_by_card: Dict[str, List[Dict[str, Any]]] = {}
        for log in attendance_logs:
            card_id = log.get('card_id')
            if card_id:
                if card_id not in logs_by_card:
                    logs_by_card[card_id] = []
                logs_by_card[card_id].append(log)
        
        # Step 3: Build attendance records for each employee
        employee_attendances: List[EmployeeAttendance] = []
        
        # Counters for summary
        present_count = 0
        absent_count = 0
        early_in_count = 0
        on_time_count = 0
        late_entry_count = 0
        
        for employee in employees:
            user_id = employee.get('user_id')
            user = users.get(user_id)
            
            if not user:
                # Skip if user doesn't exist or is deleted
                continue
            
            # Get employee details
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            employee_name = f"{first_name} {last_name}".strip()
            
            dep_id = employee.get('dep_id')
            department_name = departments.get(dep_id, {}).get('name') if dep_id else None
            
            rfid_value = employee.get('rfid_value')
            
            # Get attendance logs for this employee's RFID
            employee_logs = logs_by_card.get(rfid_value, []) if rfid_value else []
            
            # Calculate attendance data
            clock_in = _get_first_clock_in(employee_logs)
            clock_out = _get_last_clock_out(employee_logs)
            total_hours = _calculate_total_hours(employee_logs)
            status = _determine_status(clock_in)
            tap_count = len(employee_logs)
            
            # Update counters
            if status == AttendanceStatus.ABSENT:
                absent_count += 1
            else:
                present_count += 1
                if status == AttendanceStatus.EARLY_IN:
                    early_in_count += 1
                elif status == AttendanceStatus.ON_TIME:
                    on_time_count += 1
                elif status == AttendanceStatus.LATE_ENTRY:
                    late_entry_count += 1
            
            # Build attendance record
            attendance = EmployeeAttendance(
                user_id=user_id,
                employee_name=employee_name,
                department_name=department_name,
                rfid_value=rfid_value,
                attendance_date=target_date,
                clock_in=clock_in,
                clock_out=clock_out,
                total_hours=total_hours,
                status=status,
                tap_count=tap_count,
            )
            employee_attendances.append(attendance)
        
        # Build summary
        total_employees = len(employee_attendances)
        summary = AttendanceSummary(
            summary_date=target_date,
            total_employees=total_employees,
            present=present_count,
            absent=absent_count,
            early_in=early_in_count,
            on_time=on_time_count,
            late_entry=late_entry_count,
        )
        
        return DailyAttendanceResponse(
            response_date=target_date,
            summary=summary,
            employees=employee_attendances,
        )
    
    except Exception as e:
        logger.error(f"Error getting attendance: {str(e)}")
        raise Exception(f"Error getting attendance: {str(e)}")


async def get_employee_attendance(user_id: str, target_date: Optional[date] = None) -> Optional[EmployeeAttendance]:
    """
    Get attendance for a specific employee.
    
    Args:
        user_id: The employee's user UUID
        target_date: The date to get attendance for (defaults to today)
    
    Returns:
        EmployeeAttendance or None if employee not found
    """
    if target_date is None:
        target_date = date.today()
    
    try:
        # Get employee
        employee_response = supabase_client.table('employees').select('*').eq('user_id', user_id).execute()
        if not employee_response.data:
            return None
        employee = employee_response.data[0]
        
        # Get user
        user_response = supabase_client.table('users').select('*').eq('user_id', user_id).is_('deleted_at', 'null').execute()
        if not user_response.data:
            return None
        user = user_response.data[0]
        
        # Get department
        dep_id = employee.get('dep_id')
        department_name = None
        if dep_id:
            dep_response = supabase_client.table('departments').select('name').eq('dep_id', dep_id).execute()
            if dep_response.data:
                department_name = dep_response.data[0].get('name')
        
        # Get attendance logs
        rfid_value = employee.get('rfid_value')
        employee_logs = []
        if rfid_value:
            employee_logs = await opensearch_client.get_attendance_by_card_id(rfid_value, target_date)
        
        # Calculate attendance data
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        employee_name = f"{first_name} {last_name}".strip()
        
        clock_in = _get_first_clock_in(employee_logs)
        clock_out = _get_last_clock_out(employee_logs)
        total_hours = _calculate_total_hours(employee_logs)
        status = _determine_status(clock_in)
        
        return EmployeeAttendance(
            user_id=user_id,
            employee_name=employee_name,
            department_name=department_name,
            rfid_value=rfid_value,
            attendance_date=target_date,
            clock_in=clock_in,
            clock_out=clock_out,
            total_hours=total_hours,
            status=status,
            tap_count=len(employee_logs),
        )
    
    except Exception as e:
        logger.error(f"Error getting employee attendance: {str(e)}")
        raise Exception(f"Error getting employee attendance: {str(e)}")


# Department colors for chart (matching the UI)
DEPARTMENT_COLORS = {
    "Human Resources": "#6366f1",
    "IT Department": "#22c55e", 
    "Web Development": "#3b82f6",
    "Software Development": "#06b6d4",
    "Digital Marketing Specialists": "#ef4444",
    "Graphics Design Department": "#f59e0b",
    "Motion Graphics Design": "#8b5cf6",
    "Technical Support": "#14b8a6",
}


async def get_employee_distribution(target_date: Optional[date] = None) -> EmployeeDistributionResponse:
    """
    Get employee distribution by department for pie chart.
    Shows present employees grouped by department + absent count.
    
    Args:
        target_date: The date to get distribution for (defaults to today)
    
    Returns:
        EmployeeDistributionResponse with distribution data for pie chart
    """
    if target_date is None:
        target_date = date.today()
    
    try:
        # Get attendance data for the day
        attendance_data = await get_attendance_by_date(target_date)
        
        # Group present employees by department
        department_counts: Dict[str, int] = {}
        absent_count = 0
        
        for emp in attendance_data.employees:
            if emp.status == AttendanceStatus.ABSENT:
                absent_count += 1
            else:
                dept_name = emp.department_name or "Unassigned"
                department_counts[dept_name] = department_counts.get(dept_name, 0) + 1
        
        # Build distribution list
        distribution = []
        for dept_name, count in sorted(department_counts.items(), key=lambda x: -x[1]):
            distribution.append(DepartmentDistribution(
                department_name=dept_name,
                count=count,
                color=DEPARTMENT_COLORS.get(dept_name),
            ))
        
        # Add absent as a category
        if absent_count > 0:
            distribution.append(DepartmentDistribution(
                department_name="Absent",
                count=absent_count,
                color="#9ca3af",  # Gray color for absent
            ))
        
        return EmployeeDistributionResponse(
            total_employees=attendance_data.summary.total_employees,
            present=attendance_data.summary.present,
            absent=attendance_data.summary.absent,
            distribution=distribution,
        )
    
    except Exception as e:
        logger.error(f"Error getting employee distribution: {str(e)}")
        raise Exception(f"Error getting employee distribution: {str(e)}")

