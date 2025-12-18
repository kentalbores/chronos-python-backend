from pydantic import BaseModel, Field


class InputRequest(BaseModel):
    """
    Model for input data validation and serialization.
    Inherits from Pydantic's BaseModel for data validation.
    """

    name: str = Field(..., description="Your name")
