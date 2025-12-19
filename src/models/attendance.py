from typing import Optional, List
from datetime import date as date_type, datetime, time
from enum import Enum
from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    """Attendance status enum."""
    EARLY_IN = "early-in"
    ON_TIME = "on-time"
    LATE_ENTRY = "late-entry"
    ABSENT = "absent"


class AttendanceRecord(BaseModel):
    """Model for a single attendance record from OpenSearch."""
    card_id: str
    event_type: str  # "tap-in" or "tap-out"
    timestamp: datetime


class EmployeeAttendance(BaseModel):
    """Model for employee attendance response."""
    # Employee info
    user_id: str = Field(..., description="Employee's user UUID")
    employee_name: str = Field(..., description="Employee's full name")
    department_name: Optional[str] = Field(None, description="Department name")
    rfid_value: Optional[str] = Field(None, description="Employee's RFID card value")
    
    # Attendance info
    attendance_date: date_type = Field(..., description="Attendance date")
    clock_in: Optional[datetime] = Field(None, description="First tap-in timestamp")
    clock_out: Optional[datetime] = Field(None, description="Last tap-out timestamp")
    total_hours: Optional[float] = Field(None, description="Total hours worked")
    status: AttendanceStatus = Field(..., description="Attendance status")
    
    # Additional details
    tap_count: int = Field(0, description="Total number of taps for the day")


class AttendanceSummary(BaseModel):
    """Model for attendance summary statistics."""
    summary_date: date_type
    total_employees: int
    present: int
    absent: int
    early_in: int
    on_time: int
    late_entry: int


class DailyAttendanceResponse(BaseModel):
    """Model for daily attendance response."""
    response_date: date_type
    summary: AttendanceSummary
    employees: List[EmployeeAttendance]


class DepartmentDistribution(BaseModel):
    """Model for department distribution in pie chart."""
    department_name: str = Field(..., description="Department name")
    count: int = Field(..., description="Number of employees present from this department")
    color: Optional[str] = Field(None, description="Optional color for chart")


class EmployeeDistributionResponse(BaseModel):
    """Model for employee distribution chart data."""
    total_employees: int = Field(..., description="Total number of employees")
    present: int = Field(..., description="Number of present employees")
    absent: int = Field(..., description="Number of absent employees")
    distribution: List[DepartmentDistribution] = Field(..., description="Distribution by department")

