from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class Gender(str, Enum):
    """Gender options for user profile."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class ProfileCompletionStatus(str, Enum):
    """Profile completion status."""
    INCOMPLETE = "incomplete"
    BASIC = "basic"
    COMPLETE = "complete"
    VERIFIED = "verified"


class UserProfileCreate(BaseModel):
    """Model for creating user profile."""
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    date_of_birth: Optional[datetime] = Field(None, description="User's date of birth")
    gender: Optional[Gender] = Field(None, description="User's gender")
    country: Optional[str] = Field(None, max_length=100, description="User's country")
    city: Optional[str] = Field(None, max_length=100, description="User's city")
    address: Optional[str] = Field(None, max_length=500, description="User's address")
    postal_code: Optional[str] = Field(None, max_length=20, description="User's postal code")
    profile_picture_url: Optional[str] = Field(None, description="URL to user's profile picture")
    bio: Optional[str] = Field(None, max_length=1000, description="User's bio/description")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        # Remove extra spaces and ensure proper formatting
        return ' '.join(v.strip().split())
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        """Validate postal code format."""
        if v:
            # Basic postal code validation (alphanumeric, 3-10 characters)
            if not re.match(r'^[A-Za-z0-9\s-]{3,10}$', v):
                raise ValueError('Invalid postal code format')
        return v


class UserProfileUpdate(BaseModel):
    """Model for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[Gender] = None
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=1000)
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            return ' '.join(v.strip().split())
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth."""
        if v:
            # Handle timezone-aware datetime comparison
            from datetime import timezone
            if v.tzinfo is None:
                # If input is timezone-naive, make it timezone-aware (UTC)
                v = v.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            if v > now:
                raise ValueError('Date of birth cannot be in the future')
            age = (now - v).days // 365
            if age < 13:
                raise ValueError('User must be at least 13 years old')
        return v
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        """Validate postal code format."""
        if v:
            if not re.match(r'^[A-Za-z0-9\s-]{3,10}$', v):
                raise ValueError('Invalid postal code format')
        return v


class UserProfileResponse(BaseModel):
    """Model for user profile response."""
    user_id: str = Field(..., description="User ID")
    phone_number: str = Field(..., description="User's phone number")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    email: Optional[str] = Field(None, description="User's email address")
    date_of_birth: Optional[datetime] = Field(None, description="User's date of birth")
    gender: Optional[Gender] = Field(None, description="User's gender")
    country: Optional[str] = Field(None, description="User's country")
    city: Optional[str] = Field(None, description="User's city")
    address: Optional[str] = Field(None, description="User's address")
    postal_code: Optional[str] = Field(None, description="User's postal code")
    profile_picture_url: Optional[str] = Field(None, description="URL to user's profile picture")
    bio: Optional[str] = Field(None, description="User's bio/description")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    profile_completion_status: ProfileCompletionStatus = Field(..., description="Profile completion status")
    profile_completion_percentage: int = Field(0, description="Profile completion percentage")
    is_verified: bool = Field(..., description="Whether user is verified")
    status: UserStatus = Field(..., description="User account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class ProfileCompletionRequest(BaseModel):
    """Model for profile completion request."""
    profile_data: UserProfileCreate = Field(..., description="Complete profile data")


class ProfileCompletionResponse(BaseModel):
    """Model for profile completion response."""
    success: bool = Field(..., description="Whether profile was completed successfully")
    message: str = Field(..., description="Response message")
    profile_completion_status: ProfileCompletionStatus = Field(..., description="New completion status")
    profile_completion_percentage: int = Field(..., description="New completion percentage")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing required fields")


class ProfileStatsResponse(BaseModel):
    """Model for profile statistics response."""
    total_users: int = Field(..., description="Total number of users")
    completed_profiles: int = Field(..., description="Number of completed profiles")
    incomplete_profiles: int = Field(..., description="Number of incomplete profiles")
    verified_users: int = Field(..., description="Number of verified users")
    completion_rate: float = Field(..., description="Profile completion rate percentage")


class UserSearchRequest(BaseModel):
    """Model for user search request."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class UserSearchResponse(BaseModel):
    """Model for user search response."""
    users: List[UserProfileResponse] = Field(..., description="List of matching users")
    total_count: int = Field(..., description="Total number of matching users")
    has_more: bool = Field(..., description="Whether there are more results")


class ProfileValidationError(BaseModel):
    """Model for profile validation errors."""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(None, description="Value that failed validation")


class ProfileValidationResponse(BaseModel):
    """Model for profile validation response."""
    is_valid: bool = Field(..., description="Whether profile is valid")
    errors: List[ProfileValidationError] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
