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
    EmployeeAttendanceReport,
    AttendanceReportSummary,
    AttendanceReportResponse,
    AttendanceLog,
    DailyAttendanceSummary,
    EmployeeAttendancePeriodResponse,
)

logger = logging.getLogger(__name__)

# Time thresholds for status determination
EARLY_IN_THRESHOLD = time(9, 0, 0)    # Before 9:00 AM = early-in
ON_TIME_THRESHOLD = time(9, 15, 0)     # Before 9:30 AM = on-time


def _determine_status(clock_in_time: Optional[datetime]) -> AttendanceStatus:
    """
    Determine attendance status based on clock-in time.
    
    Rules:
    - Clock in before 9:00 AM = early-in
    - Clock in before 9:15 AM = on-time  
    - Clock in after 9:15 AM = late-entry
    - No clock-in = absent

    15 min grace period
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
        
        # Build logs list as tap-in/tap-out session pairs
        logs = []
        current_tap_in = None
        
        for log in employee_logs:
            event_type = log.get('event_type')
            timestamp_str = log.get('timestamp')
            
            if not timestamp_str:
                continue
            
            try:
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                else:
                    timestamp = timestamp_str
            except ValueError:
                continue
            
            if event_type == 'tap-in':
                # If there's a previous unclosed tap-in, close it with null tap-out
                if current_tap_in:
                    logs.append(AttendanceLog(tap_in=current_tap_in, tap_out=None))
                current_tap_in = timestamp
            elif event_type == 'tap-out' and current_tap_in:
                # Complete the session pair
                logs.append(AttendanceLog(tap_in=current_tap_in, tap_out=timestamp))
                current_tap_in = None
        
        # If there's an unclosed tap-in at the end, add it with null tap-out
        if current_tap_in:
            logs.append(AttendanceLog(tap_in=current_tap_in, tap_out=None))
        
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
            logs=logs if logs else None,
        )
    
    except Exception as e:
        logger.error(f"Error getting employee attendance: {str(e)}")
        raise Exception(f"Error getting employee attendance: {str(e)}")



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
            dept_response = supabase_client.table('departments').select('dep_color').eq('name', dept_name).execute()
            if dept_response.data:
                dept_color = dept_response.data[0].get('dep_color')
            else:
                dept_color = "#9ca3af"
            distribution.append(DepartmentDistribution(
                department_name=dept_name,
                count=count,
                color=dept_color
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


def _count_working_days(start_date: date, end_date: date) -> int:
    """
    Count the number of working days (Mon-Fri) in a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        Number of working days
    """
    working_days = 0
    current = start_date
    while current <= end_date:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday to Friday
            working_days += 1
        current += timedelta(days=1)
    return working_days


def _generate_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of dates (Mon-Fri only) in a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        List of working dates
    """
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday to Friday
            dates.append(current)
        current += timedelta(days=1)
    return dates


async def get_attendance_report(start_date: date, end_date: date) -> AttendanceReportResponse:
    """
    Get attendance report for all employees over a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        AttendanceReportResponse with aggregated attendance data per employee
    """
    try:
        # Step 1: Get all active employees from Supabase
        employees_response = supabase_client.table('employees').select('*').execute()
        employees = employees_response.data
        
        # Get all active users
        users_response = supabase_client.table('users').select('*').is_('deleted_at', 'null').execute()
        users = {user['user_id']: user for user in users_response.data}
        
        # Get all departments
        departments_response = supabase_client.table('departments').select('*').execute()
        departments = {dep['dep_id']: dep for dep in departments_response.data}
        
        # Step 2: Get all attendance logs from OpenSearch for the date range
        all_logs = await opensearch_client.get_attendance_logs_date_range(start_date, end_date)
        
        # Group logs by card_id and date
        logs_by_card_date: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for log in all_logs:
            card_id = log.get('card_id')
            timestamp_str = log.get('timestamp')
            
            if not card_id or not timestamp_str:
                continue
            
            # Parse date from timestamp
            try:
                if isinstance(timestamp_str, str):
                    log_dt = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                else:
                    log_dt = timestamp_str
                log_date_str = log_dt.date().isoformat()
            except ValueError:
                continue
            
            if card_id not in logs_by_card_date:
                logs_by_card_date[card_id] = {}
            if log_date_str not in logs_by_card_date[card_id]:
                logs_by_card_date[card_id][log_date_str] = []
            logs_by_card_date[card_id][log_date_str].append(log)
        
        # Step 3: Generate working days list
        working_days = _generate_date_range(start_date, end_date)
        total_working_days = len(working_days)
        
        # Step 4: Build report for each employee
        employee_reports: List[EmployeeAttendanceReport] = []
        
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
            
            # Initialize counters
            presents = 0
            lates = 0
            absences = 0
            total_hours = 0.0
            
            # Get logs for this employee's RFID
            employee_logs_by_date = logs_by_card_date.get(rfid_value, {}) if rfid_value else {}
            
            # Process each working day
            for work_date in working_days:
                date_str = work_date.isoformat()
                day_logs = employee_logs_by_date.get(date_str, [])
                
                # Get first clock-in for status determination
                clock_in = _get_first_clock_in(day_logs)
                status = _determine_status(clock_in)
                
                # Calculate hours for this day
                day_hours = _calculate_total_hours(day_logs)
                
                # Don't add ongoing hours for past days that have no clock-out
                # (the _calculate_total_hours already handles "still clocked in" logic, 
                # but for past days we should only count completed sessions)
                if work_date < date.today() and day_logs:
                    # Recalculate for past days without "still clocked in" logic
                    day_hours = _calculate_completed_hours(day_logs)
                
                if day_hours:
                    total_hours += day_hours
                
                # Update counters based on status
                if status == AttendanceStatus.ABSENT:
                    absences += 1
                else:
                    presents += 1
                    if status == AttendanceStatus.LATE_ENTRY:
                        lates += 1
            


            # Attendance Score Calculation
            attendance_score = (presents / (presents + lates + absences))*100 
            late_penalty = lates * 0.5
            total_attendance_score = attendance_score - late_penalty

            if total_attendance_score > 90:
                performance = 'Excellent'
            elif total_attendance_score > 80:
                performance = 'Fair'
            elif total_attendance_score > 70:
                performance = 'Poor'
            else:
                performance = 'Very Poor'
            

            # Build report for this employee
            report = EmployeeAttendanceReport(
                user_id=user_id,
                employee_name=employee_name,
                department_name=department_name,
                presents=presents,
                lates=lates,
                absences=absences,
                total_hours=round(total_hours, 2),
                total_attendance_score=total_attendance_score,
                performance=performance,
            )
            employee_reports.append(report)
        
        # Build summary
        summary = AttendanceReportSummary(
            start_date=start_date,
            end_date=end_date,
            total_working_days=total_working_days,
            total_employees=len(employee_reports),
        )
        
        return AttendanceReportResponse(
            summary=summary,
            employees=employee_reports,
        )
    
    except Exception as e:
        logger.error(f"Error getting attendance report: {str(e)}")
        raise Exception(f"Error getting attendance report: {str(e)}")


def _calculate_completed_hours(logs: List[Dict[str, Any]]) -> float:
    """
    Calculate completed hours from attendance logs (for past days).
    Only counts tap-in/tap-out pairs, ignores unclosed sessions.
    
    Args:
        logs: List of attendance logs for a single day
    
    Returns:
        Total completed hours
    """
    if not logs:
        return 0.0
    
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
            total_seconds += max(0, duration)
            current_tap_in = None
    
    # Don't count unclosed sessions for past days
    return round(total_seconds / 3600, 2)


def _get_week_range() -> tuple[date, date]:
    """Get the start and end date of the current week (Monday to Sunday)."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week


def _get_month_range() -> tuple[date, date]:
    """Get the start and end date of the current month."""
    today = date.today()
    start_of_month = today.replace(day=1)
    # Get last day of month
    if today.month == 12:
        end_of_month = today.replace(day=31)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return start_of_month, end_of_month


async def get_employee_attendance_period(
    user_id: str,
    period: str  # "week" or "month"
) -> Optional[EmployeeAttendancePeriodResponse]:
    """
    Get attendance for a specific employee over a period (this week or this month).
    
    Args:
        user_id: The employee's user UUID
        period: "week" for this week, "month" for this month
    
    Returns:
        EmployeeAttendancePeriodResponse or None if employee not found
    """
    if period == "week":
        start_date, end_date = _get_week_range()
    elif period == "month":
        start_date, end_date = _get_month_range()
    else:
        raise ValueError("Period must be 'week' or 'month'")
    
    return await get_employee_attendance_range(user_id, start_date, end_date)


async def get_employee_attendance_range(
    user_id: str,
    start_date: date,
    end_date: date
) -> Optional[EmployeeAttendancePeriodResponse]:
    """
    Get attendance for a specific employee over a date range.
    
    Args:
        user_id: The employee's user UUID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        EmployeeAttendancePeriodResponse or None if employee not found
    """
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
        
        # Get employee details
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        employee_name = f"{first_name} {last_name}".strip()
        
        rfid_value = employee.get('rfid_value')
        
        # Get all attendance logs for the date range
        all_logs = []
        if rfid_value:
            all_logs = await opensearch_client.get_attendance_logs_date_range(start_date, end_date)
            # Filter logs for this employee's RFID
            all_logs = [log for log in all_logs if log.get('card_id') == rfid_value]
        
        # Group logs by date
        logs_by_date: Dict[str, List[Dict[str, Any]]] = {}
        for log in all_logs:
            timestamp_str = log.get('timestamp')
            if not timestamp_str:
                continue
            
            try:
                if isinstance(timestamp_str, str):
                    log_dt = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                else:
                    log_dt = timestamp_str
                log_date_str = log_dt.date().isoformat()
            except ValueError:
                continue
            
            if log_date_str not in logs_by_date:
                logs_by_date[log_date_str] = []
            logs_by_date[log_date_str].append(log)
        
        # Generate working days list
        working_days = _generate_date_range(start_date, end_date)
        total_working_days = len(working_days)
        
        # Initialize counters
        presents = 0
        lates = 0
        absences = 0
        total_hours = 0.0
        daily_attendance: List[DailyAttendanceSummary] = []
        
        # Process each working day
        for work_date in working_days:
            date_str = work_date.isoformat()
            day_logs = logs_by_date.get(date_str, [])
            
            # Get clock in/out times
            clock_in = _get_first_clock_in(day_logs)
            clock_out = _get_last_clock_out(day_logs)
            status = _determine_status(clock_in)
            
            # Calculate hours for this day
            if work_date < date.today() and day_logs:
                # For past days, only count completed sessions
                day_hours = _calculate_completed_hours(day_logs)
            else:
                day_hours = _calculate_total_hours(day_logs)
            
            if day_hours:
                total_hours += day_hours
            
            # Update counters based on status
            if status == AttendanceStatus.ABSENT:
                absences += 1
            else:
                presents += 1
                if status == AttendanceStatus.LATE_ENTRY:
                    lates += 1
            
            # Add daily summary
            daily_attendance.append(DailyAttendanceSummary(
                date=work_date,
                clock_in=clock_in,
                clock_out=clock_out,
                total_hours=day_hours,
                status=status,
            ))
        
        return EmployeeAttendancePeriodResponse(
            user_id=user_id,
            employee_name=employee_name,
            department_name=department_name,
            start_date=start_date,
            end_date=end_date,
            total_working_days=total_working_days,
            presents=presents,
            lates=lates,
            absences=absences,
            total_hours=round(total_hours, 2),
            daily_attendance=daily_attendance,
        )
    
    except Exception as e:
        logger.error(f"Error getting employee attendance range: {str(e)}")
        raise Exception(f"Error getting employee attendance range: {str(e)}")

