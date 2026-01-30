from typing import Optional
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class LeaveRequestBase(BaseModel):
    """Base model for leave request data."""
    type: str = Field(..., description="Type of leave (e.g., Sick Leave, Vacation Leave)")
    start_date: date = Field(..., description="Start date of the leave")
    end_date: date = Field(..., description="End date of the leave")
    comment: Optional[str] = Field(None, description="Reason or comment for the leave request")
    attachment_url: Optional[str] = Field(None, description="URL of any attached document")


class LeaveRequestCreate(LeaveRequestBase):
    """Model for creating a new leave request."""
    user_id: str = Field(..., description="UUID of the user requesting leave")


class LeaveRequestUpdate(BaseModel):
    """Model for updating a leave request (e.g., status update by admin)."""
    status: Optional[str] = Field(None, description="New status (e.g., Approved, Rejected)")
    approved_by: Optional[str] = Field(None, description="UUID of the admin approving/rejecting")


class LeaveRequestFilter(BaseModel):
    """Model for filtering leave requests."""
    user_id: Optional[str] = Field(None, description="Filter by User ID")
    status: Optional[str] = Field(None, description="Filter by status")
    type: Optional[str] = Field(None, description="Filter by leave type")
    date_from: Optional[date] = Field(None, description="Filter by start date (from)")
    date_to: Optional[date] = Field(None, description="Filter by start date (to)")
    
    # Pagination
    limit: Optional[int] = Field(100, ge=1, le=500, description="Max number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")


class LeaveRequestResponse(LeaveRequestBase):
    """Model for leave request response with user and department details."""
    leave_id: str = Field(..., description="UUID of the leave request")
    user_id: str = Field(..., description="UUID of the user")
    status: str = Field(..., description="Status of the request")
    created_at: datetime = Field(..., description="Date requested")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    approved_by: Optional[str] = Field(None, description="UUID of the approver")
    deleted_at: Optional[date] = Field(None, description="Soft delete timestamp")
    
    # Enriched fields for UI
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    dep_name: Optional[str] = Field(None, description="Department name")
    profile_url: Optional[str] = Field(None, description="User's profile picture URL")
