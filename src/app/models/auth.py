from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class PhoneNumberRequest(BaseModel):
    """Request model for sending OTP to phone number."""
    phone_number: str = Field(..., description="Phone number in international format (e.g., +1234567890)")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Check if it starts with + and has 10-15 digits
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValueError('Phone number must be in international format (e.g., +1234567890)')
        
        return cleaned


class OTPVerificationRequest(BaseModel):
    """Request model for OTP verification."""
    phone_number: str = Field(..., description="Phone number in international format")
    otp_code: str = Field(..., min_length=4, max_length=8, description="OTP code received")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValueError('Phone number must be in international format (e.g., +1234567890)')
        return cleaned


class LoginRequest(BaseModel):
    """Request model for login with phone number and OTP."""
    phone_number: str = Field(..., description="Phone number in international format")
    otp_code: str = Field(..., min_length=4, max_length=8, description="OTP code")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValueError('Phone number must be in international format (e.g., +1234567890)')
        return cleaned


class OTPResponse(BaseModel):
    """Response model for OTP sending."""
    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Response message")
    expires_in: int = Field(..., description="OTP expiry time in seconds")
    retry_after: int = Field(..., description="Time to wait before retry in seconds")


class AuthTokenResponse(BaseModel):
    """Response model for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    user_id: str = Field(..., description="User ID")
    phone_number: str = Field(..., description="User's phone number")
    is_new_user: bool = Field(..., description="Whether this is a new user")
    profile_exists: bool = Field(..., description="Whether user has a complete profile")
    profile_completion_required: bool = Field(..., description="Whether profile completion is required")


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Unique user ID")
    phone_number: str = Field(..., description="User's phone number")
    is_verified: bool = Field(..., description="Whether phone number is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Request model for logout."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


class AuthErrorResponse(BaseModel):
    """Error response model for authentication failures."""
    success: bool = Field(default=False, description="Success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
