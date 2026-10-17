from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.publication import (
    PublicationStatus,
    PublicationType,
)


class PublicationCreate(BaseModel):
    type: PublicationType
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10)
    looking_for: str = Field(min_length=2)


class PublicationUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=150,
    )
    description: Optional[str] = Field(
        default=None,
        min_length=10,
    )
    looking_for: Optional[str] = Field(
        default=None,
        min_length=2,
    )
    status: Optional[PublicationStatus] = None


class PublicationResponse(BaseModel):
    id: int
    author_id: int
    type: PublicationType
    title: str
    description: str
    looking_for: str
    status: PublicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)