"""
ClimaScope - User Model
Defines user data structures and validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")

class UserCreate(UserBase):
    """User model for registration"""
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

class UserInDB(UserBase):
    """User model as stored in database"""
    id: str = Field(..., description="User ID")
    password: str = Field(..., description="Hashed password")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(True, description="Account status")
    role: str = Field("user", description="User role")

class UserResponse(BaseModel):
    """User model for API responses (without password)"""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    created_at: datetime = Field(..., description="Account creation timestamp")

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class UserUpdate(BaseModel):
    """User model for updates"""
    full_name: Optional[str] = Field(None, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    current_password: Optional[str] = Field(None, description="Current password for verification")
    new_password: Optional[str] = Field(None, min_length=8, description="New password (min 8 characters)")
