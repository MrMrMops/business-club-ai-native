from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    skills: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    bio: Optional[str]
    skills: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"