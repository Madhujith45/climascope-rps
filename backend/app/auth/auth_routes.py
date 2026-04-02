"""
ClimaScope - Authentication Routes
Handles user signup, login, token management, and OTP password reset.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging
from datetime import datetime
from bson import ObjectId

from .jwt_handler import create_access_token, verify_token, hash_password, verify_password
from ..db.mongo import get_mongo_db
from ..db.models.user import UserCreate
from ..utils.otp import create_otp_record, verify_otp, verify_reset_token, consume_reset_token
from ..utils.email import send_otp_email
from ..utils.rate_limiter import otp_limiter, login_limiter, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# ── Pydantic models ──────────────────────────────────────────────────────

class UserSignup(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User full name")
    phone: Optional[str] = Field(None, description="Optional phone number for SMS alerts")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User information")

class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")
    created_at: datetime = Field(..., description="Account creation timestamp")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")

class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email used for OTP request")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email used for OTP request")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")
    reset_token: str = Field(..., description="Reset token from OTP verification")


# ── Dependencies ─────────────────────────────────────────────────────────

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user
    """
    if not credentials or not credentials.scheme or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    db = get_mongo_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# ── Signup ───────────────────────────────────────────────────────────────

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup):
    """
    Register a new user account
    """
    try:
        db = get_mongo_db()
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_create = UserCreate(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone=user_data.phone if hasattr(user_data, "phone") else None,
            alert_mode=user_data.alert_mode if hasattr(user_data, "alert_mode") else "email",
            alerts_enabled=user_data.alerts_enabled if hasattr(user_data, "alerts_enabled") else True
        )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Prepare user document
        user_doc = {
            "email": user_create.email,
            "password": hashed_password,
            "full_name": user_create.full_name,
            "phone": user_create.phone,
            "alert_mode": user_create.alert_mode,
            "alerts_enabled": user_create.alerts_enabled,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "role": "user"
        }

        # Insert into database
        result = await db.users.insert_one(user_doc)

        # Return user response (without password)
        response_user = {
            "id": str(result.inserted_id),
            "email": user_create.email,
            "full_name": user_create.full_name,
            "phone": user_create.phone,
            "alert_mode": user_create.alert_mode,
            "alerts_enabled": user_create.alerts_enabled,
            "created_at": user_doc["created_at"]
        }
        return response_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


# ── Login (rate-limited) ─────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin, request: Request):
    """
    Authenticate user and return JWT token.
    Rate limited: max 5 attempts per minute per IP.
    """
    client_ip = get_client_ip(request)
    login_limiter.check_and_record(client_ip)

    try:
        db = get_mongo_db()
        
        # Find user by email
        user = await db.users.find_one({"email": user_credentials.email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token
        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role", "user")
        }
        
        access_token = create_access_token(token_data)
        
        # Prepare user info for response (without password)
        user_info = {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role", "user")
        }
        
        logger.info(f"User logged in: {user_credentials.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# ── Password Reset: OTP Flow ────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, request: Request):
    """Step 1: Request a password reset OTP.

    Generates a 6-digit OTP, stores it hashed in MongoDB, and sends it
    via email (or logs it in dev mode if SMTP is not configured).

    Rate limited: max 3 requests per minute per IP.
    """
    client_ip = get_client_ip(request)
    otp_limiter.check_and_record(client_ip)

    db = get_mongo_db()
    user = await db.users.find_one({"email": body.email})

    # Always return success to avoid email enumeration
    if not user:
        logger.warning("OTP requested for non-existent email: %s", body.email)
        return {"message": "If the email is registered, an OTP has been sent."}

    # Generate and store OTP
    otp = await create_otp_record(body.email)

    # Send OTP via email (falls back to console print in dev mode if SMTP not configured)
    email_sent = send_otp_email(body.email, otp)
    if not email_sent:
        logger.error("Failed to send OTP email to %s – check SMTP configuration", body.email)
    else:
        logger.info("OTP dispatch complete for %s (check console if SMTP is not configured)", body.email)

    return {"message": "If the email is registered, an OTP has been sent."}


@router.post("/verify-otp")
async def verify_otp_endpoint(body: VerifyOTPRequest, request: Request):
    """Step 2: Verify the 6-digit OTP.

    On success, returns a temporary reset token needed for step 3.
    Max 5 verification attempts per OTP.
    """
    client_ip = get_client_ip(request)
    otp_limiter.check_and_record(client_ip)

    success, reset_token, message = await verify_otp(body.email, body.otp)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {
        "message": message,
        "reset_token": reset_token,
    }


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """Step 3: Reset password using the reset token from step 2.

    Validates the reset token, hashes the new password, and updates
    the user record. The OTP record is then deleted.
    """
    # Verify reset token
    valid = await verify_reset_token(body.email, body.reset_token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please restart the process.",
        )

    # Update password
    db = get_mongo_db()
    hashed = hash_password(body.new_password)
    result = await db.users.update_one(
        {"email": body.email},
        {"$set": {"password": hashed, "updated_at": datetime.utcnow()}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Consume the reset token
    await consume_reset_token(body.email, body.reset_token)

    logger.info("Password reset successfully for email=%s", body.email)
    return {"message": "Password has been reset successfully. Please login with your new password."}


# ── Profile & Session ────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "phone": current_user.get("phone"),
        "alert_mode": current_user.get("alert_mode", "email"),
        "alerts_enabled": current_user.get("alerts_enabled", True),
        "created_at": current_user.get("created_at", datetime.utcnow())
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client-side token removal)
    """
    logger.info(f"User logged out: {current_user['email']}")
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_user_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if token is valid
    """
    return {
        "valid": True,
        "user": {
            "id": str(current_user["_id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name"),
            "phone": current_user.get("phone"),
            "alert_mode": current_user.get("alert_mode", "email"),
            "alerts_enabled": current_user.get("alerts_enabled", True)
        }
    }

from ..db.models.user import UserUpdate
@router.put("/me/settings", response_model=dict)
async def update_settings(update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = get_mongo_db()
    update_fields = {}
    if update_data.phone is not None:
        update_fields["phone"] = update_data.phone
    if update_data.alert_mode is not None:
        update_fields["alert_mode"] = update_data.alert_mode
    if update_data.alerts_enabled is not None:
        update_fields["alerts_enabled"] = update_data.alerts_enabled
    if update_data.full_name is not None:
        update_fields["full_name"] = update_data.full_name

    if not update_fields:
        return {"message": "No updates provided"}

    update_fields["updated_at"] = datetime.utcnow()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_fields}
    )

    return {"message": "Settings updated successfully"}
