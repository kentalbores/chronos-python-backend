from typing import Optional
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base model for department data."""
    name: str = Field(..., description="Department name")


class DepartmentCreate(DepartmentBase):
    """Model for creating a new department."""
    pass


class DepartmentUpdate(BaseModel):
    """Model for updating an existing department."""
    dep_id: int = Field(..., description="Department ID to update")
    name: str = Field(..., description="New department name")


class DepartmentResponse(BaseModel):
    """Model for department response."""
    dep_id: int
    name: str


class DepartmentDeleteRequest(BaseModel):
    """Model for delete department request."""
    dep_id: int = Field(..., description="Department ID to delete")

