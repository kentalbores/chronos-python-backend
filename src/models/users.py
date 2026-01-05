from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base model for user data."""
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    profile_url: Optional[str] = Field(None, description="User's profile picture URL")


class UserCreate(UserBase):
    """Model for creating a new user with employee details."""
    # Auth0 credentials - password is used to create Auth0 account
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (min 8 chars, for Auth0)")
    work_status: Optional[str] = Field(None, description="Work status (e.g., on_site, wfh)")
    has_rfid: Optional[bool] = Field(False, description="Whether user has RFID")
    rfid_value: Optional[str] = Field(None, description="RFID value")
    contact_number: Optional[str] = Field(None, description="Contact phone number")
    birth_date: Optional[date] = Field(None, description="Date of birth")
    emergency_contact_number: Optional[str] = Field(None, description="Emergency contact number")
    emergency_contact_person: Optional[str] = Field(None, description="Emergency contact person name")
    shift_type: Optional[str] = Field(None, description="Shift type (day, night)")
    employee_note: Optional[str] = Field(None, description="Notes about the employee")
    date_hired: Optional[date] = Field(None, description="Date when employee was hired")
    address: Optional[str] = Field(None, description="Employee's address")
    dep_id: Optional[int] = Field(None, description="Department ID")
    leaves_used: Optional[int] = Field(0, description="Number of leaves used")
    remote_days_used: Optional[int] = Field(0, description="Number of remote days used")


class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    profile_url: Optional[str] = Field(None, description="User's profile picture URL")
    # Employee details
    email: Optional[str] = Field(None, description="User's email address")
    work_status: Optional[str] = Field(None, description="Work status")
    has_rfid: Optional[bool] = Field(None, description="Whether user has RFID")
    rfid_value: Optional[str] = Field(None, description="RFID value")
    contact_number: Optional[str] = Field(None, description="Contact phone number")
    birth_date: Optional[date] = Field(None, description="Date of birth")
    emergency_contact_number: Optional[str] = Field(None, description="Emergency contact number")
    emergency_contact_person: Optional[str] = Field(None, description="Emergency contact person name")
    shift_type: Optional[str] = Field(None, description="Shift type")
    employee_note: Optional[str] = Field(None, description="Notes about the employee")
    date_hired: Optional[date] = Field(None, description="Date when employee was hired")
    address: Optional[str] = Field(None, description="Employee's address")
    dep_id: Optional[int] = Field(None, description="Department ID")
    leaves_used: Optional[int] = Field(None, description="Number of leaves used")
    remote_days_used: Optional[int] = Field(None, description="Number of remote days used")


class CombinedUserResponse(BaseModel):
    """
    Model for combined user response with employee, intern, and department details.
    Different fields are present based on employment_type (Intern vs Regular).
    """
    # User fields
    user_id: str = Field(..., description="User UUID")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    auth0_id: str = Field(..., description="Auth0 user ID")
    profile_url: Optional[str] = Field(None, description="User's profile picture URL")
    created_at: Optional[datetime] = Field(None, description="User creation timestamp")
    deleted_at: Optional[date] = Field(None, description="Soft delete date")
    
    # Employee fields
    work_status: Optional[str] = Field(None, description="Work status (on_site, wfh)")
    has_rfid: Optional[bool] = Field(None, description="Whether user has RFID")
    rfid_value: Optional[str] = Field(None, description="RFID value")
    email: Optional[str] = Field(None, description="User's email address")
    contact_number: Optional[str] = Field(None, description="Contact phone number")
    birth_date: Optional[date] = Field(None, description="Date of birth")
    emergency_contact_number: Optional[str] = Field(None, description="Emergency contact number")
    emergency_contact_person: Optional[str] = Field(None, description="Emergency contact person name")
    shift_type: Optional[str] = Field(None, description="Shift type (day, night)")
    employee_note: Optional[str] = Field(None, description="Notes about the employee")
    leaves_used: Optional[int] = Field(None, description="Number of leaves used")
    date_hired: Optional[date] = Field(None, description="Date when employee was hired")
    address: Optional[str] = Field(None, description="Employee's address")
    remote_days_used: Optional[int] = Field(None, description="Number of remote days used")
    dep_id: Optional[int] = Field(None, description="Department ID")
    dep_name: Optional[str] = Field(None, description="Department name")
    employment_type: str = Field(..., description="Employment type: 'Intern' or 'Regular'")
    
    # Intern-specific fields (only present for interns)
    university_name: Optional[str] = Field(None, description="University name (interns only)")
    university_advisor_name: Optional[str] = Field(None, description="University advisor name (interns only)")
    university_advisor_contact_number: Optional[str] = Field(None, description="University advisor contact (interns only)")
    university_address: Optional[str] = Field(None, description="University address (interns only)")
    university_contact_number: Optional[str] = Field(None, description="University contact number (interns only)")
    university_email: Optional[str] = Field(None, description="University email (interns only)")
    internship_start_date: Optional[date] = Field(None, description="Internship start date (interns only)")
    internship_end_date: Optional[date] = Field(None, description="Internship end date (interns only)")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate (interns only)")
    required_hours: Optional[int] = Field(None, description="Required hours (interns only)")
    hours_rendered: Optional[float] = Field(None, description="Hours rendered (interns only)")


class UserDeleteRequest(BaseModel):
    """Model for delete user request."""
    user_id: str = Field(..., description="User UUID to delete")


class UserFilter(BaseModel):
    """Model for filtering and searching users."""
    # Search (partial match)
    search: Optional[str] = Field(None, description="Search by name or email (partial match)")
    
    # Filters (exact match)
    dep_id: Optional[int] = Field(None, description="Filter by department ID")
    work_status: Optional[str] = Field(None, description="Filter by work status (on_site, wfh)")
    shift_type: Optional[str] = Field(None, description="Filter by shift type (day, night)")
    employment_type: Optional[str] = Field(None, description="Filter by employment type (Intern, Regular)")
    has_rfid: Optional[bool] = Field(None, description="Filter by RFID status")
    
    # Date filters
    date_hired_from: Optional[date] = Field(None, description="Filter by hire date (from)")
    date_hired_to: Optional[date] = Field(None, description="Filter by hire date (to)")
    
    # Pagination
    limit: Optional[int] = Field(100, ge=1, le=500, description="Max number of results (1-500)")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")
