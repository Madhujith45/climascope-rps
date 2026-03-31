"""
ClimaScope - JWT Token Handler
Manages JWT token creation, verification, and user authentication
"""

from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

# JWT Configuration
# Prefer JWT_SECRET and keep JWT_SECRET_KEY as a compatibility fallback.
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT secret is missing. Set JWT_SECRET in environment variables.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 7  # 7 days

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with user data
    
    Args:
        data: Dictionary containing user information
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.JWTError:
        return None  # Invalid token

def get_current_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if valid, None if invalid
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
