from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Any
from src.app.models.user_profile import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    ProfileCompletionRequest, ProfileCompletionResponse,
    ProfileStatsResponse, UserSearchRequest, UserSearchResponse,
    ProfileValidationResponse, ProfileValidationError
)
from src.app.api.auth.views import get_current_user
from src.services.user_profile_service import user_profile_service
from src.services.utils.exceptions import APIException
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/complete", response_model=ProfileCompletionResponse)
async def complete_user_profile(
    request: ProfileCompletionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProfileCompletionResponse:
    """
    Complete user profile with all required information.
    
    This endpoint allows users to complete their profile with detailed information
    including personal details, contact information, and preferences.
    
    Args:
        request: Profile completion request with complete profile data
        current_user: Current authenticated user
        
    Returns:
        ProfileCompletionResponse with completion status and missing fields
        
    Raises:
        HTTPException: If profile completion fails
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Completing profile for user {user_id}")
        
        # Complete the profile
        profile = await user_profile_service.complete_user_profile(user_id, request.profile_data)
        
        # Get completion status
        completion_info = await user_profile_service.get_profile_completion_status(user_id)
        
        logger.info(f"Profile completed for user {user_id}, status: {profile.profile_completion_status}")
        
        return ProfileCompletionResponse(
            success=True,
            message="Profile completed successfully",
            profile_completion_status=profile.profile_completion_status,
            profile_completion_percentage=profile.profile_completion_percentage,
            missing_fields=completion_info.get("missing_required_fields", [])
        )
        
    except APIException as e:
        logger.warning(f"API Exception in complete_user_profile: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in complete_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while completing profile"
            }
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfileResponse:
    """
    Get current user's profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserProfileResponse with user's profile information
        
    Raises:
        HTTPException: If profile retrieval fails
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting profile for user {user_id}")
        
        profile = await user_profile_service.get_user_profile_by_id(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PROFILE_NOT_FOUND",
                    "message": "User profile not found. Please complete your profile first."
                }
            )
        
        return profile
        
    except HTTPException:
        raise
    except APIException as e:
        logger.warning(f"API Exception in get_my_profile: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_my_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while fetching profile"
            }
        )


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfileResponse:
    """
    Update current user's profile information.
    
    Args:
        profile_data: Profile data to update
        current_user: Current authenticated user
        
    Returns:
        UserProfileResponse with updated profile information
        
    Raises:
        HTTPException: If profile update fails
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Updating profile for user {user_id}")
        
        profile = await user_profile_service.update_user_profile(user_id, profile_data)
        
        logger.info(f"Profile updated for user {user_id}")
        return profile
        
    except APIException as e:
        logger.warning(f"API Exception in update_my_profile: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_my_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while updating profile"
            }
        )


@router.get("/completion-status", response_model=Dict[str, Any])
async def get_profile_completion_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's profile completion status and missing fields.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with completion status and missing fields
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting completion status for user {user_id}")
        
        completion_info = await user_profile_service.get_profile_completion_status(user_id)
        
        return completion_info
        
    except APIException as e:
        logger.warning(f"API Exception in get_profile_completion_status: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_profile_completion_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while getting completion status"
            }
        )


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserSearchResponse:
    """
    Search users by name or bio.
    
    Args:
        query: Search query
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user
        
    Returns:
        UserSearchResponse with matching users
        
    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(f"Searching users with query: {query}")
        
        users, total_count = await user_profile_service.search_users(query, limit, offset)
        
        has_more = (offset + len(users)) < total_count
        
        return UserSearchResponse(
            users=users,
            total_count=total_count,
            has_more=has_more
        )
        
    except APIException as e:
        logger.warning(f"API Exception in search_users: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while searching users"
            }
        )


@router.get("/stats", response_model=ProfileStatsResponse)
async def get_profile_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProfileStatsResponse:
    """
    Get profile completion statistics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        ProfileStatsResponse with statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        logger.info("Getting profile statistics")
        
        stats = await user_profile_service.get_profile_statistics()
        
        return ProfileStatsResponse(**stats)
        
    except APIException as e:
        logger.warning(f"API Exception in get_profile_statistics: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_profile_statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while getting statistics"
            }
        )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfileResponse:
    """
    Get user profile by user ID.
    
    Args:
        user_id: User ID to get profile for
        current_user: Current authenticated user
        
    Returns:
        UserProfileResponse with user's profile information
        
    Raises:
        HTTPException: If profile retrieval fails
    """
    try:
        logger.info(f"Getting profile for user {user_id}")
        
        profile = await user_profile_service.get_user_profile_by_id(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PROFILE_NOT_FOUND",
                    "message": "User profile not found"
                }
            )
        
        return profile
        
    except HTTPException:
        raise
    except APIException as e:
        logger.warning(f"API Exception in get_user_profile: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while fetching profile"
            }
        )


@router.post("/validate", response_model=ProfileValidationResponse)
async def validate_profile_data(
    profile_data: UserProfileCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProfileValidationResponse:
    """
    Validate profile data without saving.
    
    Args:
        profile_data: Profile data to validate
        current_user: Current authenticated user
        
    Returns:
        ProfileValidationResponse with validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        logger.info("Validating profile data")
        
        errors = []
        warnings = []
        
        # Basic validation (Pydantic already handles most of this)
        try:
            # Try to create the model (this will validate)
            validated_data = UserProfileCreate(**profile_data.dict())
        except Exception as e:
            errors.append(ProfileValidationError(
                field="general",
                message=str(e),
                value=None
            ))
        
        # Additional business logic validation
        if profile_data.date_of_birth:
            age = (datetime.now() - profile_data.date_of_birth).days // 365
            if age < 18:
                warnings.append("User is under 18 years old")
        
        if profile_data.email:
            # Check if email is already in use (you might want to implement this)
            # This is just an example
            pass
        
        is_valid = len(errors) == 0
        
        return ProfileValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in validate_profile_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while validating profile"
            }
        )
