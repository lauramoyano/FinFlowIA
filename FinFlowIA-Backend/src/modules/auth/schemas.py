import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Response schema containing JWT access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Public user profile response schema."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
