from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    message: str = Field(
        min_length=3,
        max_length=2000,
    )


class ApplicationResponse(BaseModel):
    id: int
    publication_id: int
    applicant_id: int
    message: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)