"""
Auth schemas for login, registration, and token responses.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    """Schema for registering a new user."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.MEMBER


class UserResponse(BaseModel):
    """Schema for returning user data (passwords excluded)."""
    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for returning JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
