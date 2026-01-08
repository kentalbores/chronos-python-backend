from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base model for department data."""
    name: str = Field(..., description="Department name")
    dep_color: str = Field(..., description="Department hex color (e.g., #FF5733)")


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

