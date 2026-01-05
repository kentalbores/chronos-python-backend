from pydantic import BaseModel, Field


class Role(BaseModel):
    """Model for role data."""
    role_id: int = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")

