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
    phone: Optional[str] = Field(None, description="User phone number")
    alert_mode: str = Field("email", description="Alert mode: email, sms, both")
    alerts_enabled: bool = Field(True, description="Enable or disable alerts")

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
    phone: Optional[str] = Field(None, description="User phone number")
    alert_mode: str = Field("email", description="Alert mode: email, sms, both")
    alerts_enabled: bool = Field(True, description="Enable or disable alerts")
    created_at: datetime = Field(..., description="Account creation timestamp")

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class UserUpdate(BaseModel):
    """User model for updates"""
    full_name: Optional[str] = Field(None, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, description="User phone number")
    alert_mode: Optional[str] = Field(None, description="Alert mode: email, sms, both")
    alerts_enabled: Optional[bool] = Field(None, description="Enable or disable alerts")
