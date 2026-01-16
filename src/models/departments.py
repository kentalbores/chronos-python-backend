from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base model for department data."""
    name: str = Field(..., description="Department name")
    dep_color: Optional[str] = Field(default='#D3D3D3', description="Department hex color (e.g., #FF5733)")


class DepartmentCreate(DepartmentBase):
    """Model for creating a new department."""
    pass


class DepartmentUpdate(BaseModel):
    """Model for updating an existing department."""
    dep_id: int = Field(..., description="Department ID to update")
    name: Optional[str] = Field(None, description="New department name")
    dep_color: Optional[str] = Field(None, description="New department hex color")


class DepartmentResponse(BaseModel):
    """Model for department response."""
    dep_id: int
    name: str
    dep_color: Optional[str] = None
    created_at: Optional[datetime] = Field(None, description="Department creation timestamp")
    employee_count: Optional[int] = Field(0, description="Number of employees in this department")


class DepartmentDeleteRequest(BaseModel):
    """Model for delete department request."""
    dep_id: int = Field(..., description="Department ID to delete")


class DepartmentEmployee(BaseModel):
    """Model for employee in department details."""
    user_id: str = Field(..., description="Employee's user UUID")
    name: str = Field(..., description="Employee's full name")
    type: str = Field(..., description="Employee type: 'intern' or 'regular'")
    phone_num: Optional[str] = Field(None, description="Employee's contact number")
    date_hired: Optional[date] = Field(None, description="Date the employee was hired")


class DepartmentStats(BaseModel):
    """Model for department statistics."""
    employee_count: int = Field(0, description="Total number of employees in the department")
    work_from_home_count: int = Field(0, description="Number of employees currently working from home")
    on_leave_count: int = Field(0, description="Number of employees currently on leave")


class DepartmentDetailResponse(BaseModel):
    """Model for detailed department response with employees."""
    dep_id: int
    name: str
    dep_color: Optional[str] = None
    stats: DepartmentStats = Field(..., description="Department statistics")
    employees: List[DepartmentEmployee] = Field(default_factory=list, description="List of employees in the department")

