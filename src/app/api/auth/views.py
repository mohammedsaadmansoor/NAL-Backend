from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from typing import Dict, Any
from src.app.models.auth import (
    PhoneNumberRequest,
    OTPVerificationRequest,
    LoginRequest,
    OTPResponse,
    AuthTokenResponse,
    UserProfile,
    RefreshTokenRequest,
    LogoutRequest,
    AuthErrorResponse
)
from src.services.db_auth_service import db_auth_service
from src.services.utils.exceptions import APIException
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(request: PhoneNumberRequest) -> OTPResponse:
    """
    Send OTP to the provided phone number.
    
    This endpoint sends a one-time password (OTP) to the specified phone number
    for authentication purposes. The OTP is valid for 5 minutes and has a
    rate limit to prevent abuse.
    
    Args:
        request: Phone number request containing the phone number
        
    Returns:
        OTPResponse with success status and expiry information
        
    Raises:
        HTTPException: If rate limit is exceeded or OTP sending fails
    """
    try:
        logger.info(f"Sending OTP to phone number: {request.phone_number}")
        
        result = await db_auth_service.send_otp(request.phone_number)
        
        logger.info(f"OTP sent successfully to {request.phone_number}")
        return OTPResponse(**result)
        
    except APIException as e:
        logger.warning(f"API Exception in send_otp: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in send_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred while sending OTP"
            ).dict()
        )


@router.post("/verify-otp", response_model=Dict[str, Any])
async def verify_otp(request: OTPVerificationRequest) -> Dict[str, Any]:
    """
    Verify the OTP code for the provided phone number.
    
    This endpoint verifies the OTP code sent to the phone number.
    The OTP must be verified within 5 minutes and has a maximum of 3 attempts.
    
    Args:
        request: OTP verification request containing phone number and OTP code
        
    Returns:
        Dict with verification result
        
    Raises:
        HTTPException: If OTP is invalid, expired, or max attempts exceeded
    """
    try:
        logger.info(f"Verifying OTP for phone number: {request.phone_number}")
        
        result = await db_auth_service.verify_otp(request.phone_number, request.otp_code)
        
        logger.info(f"OTP verified successfully for {request.phone_number}")
        return result
        
    except APIException as e:
        logger.warning(f"API Exception in verify_otp: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in verify_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred while verifying OTP"
            ).dict()
        )


@router.post("/login", response_model=AuthTokenResponse)
async def login(request: LoginRequest) -> AuthTokenResponse:
    """
    Login with phone number and OTP to get authentication tokens.
    
    This endpoint performs a complete login flow:
    1. Verifies the OTP code
    2. Creates or retrieves the user account
    3. Generates JWT access and refresh tokens
    
    Args:
        request: Login request containing phone number and OTP code
        
    Returns:
        AuthTokenResponse with access token, refresh token, and user information
        
    Raises:
        HTTPException: If OTP verification fails or login process fails
    """
    try:
        logger.info(f"Login attempt for phone number: {request.phone_number}")
        
        # Verify OTP first
        await db_auth_service.verify_otp(request.phone_number, request.otp_code)
        
        # Create or get user
        user = await db_auth_service.create_or_get_user(request.phone_number)
        
        # Generate tokens
        tokens = db_auth_service.generate_tokens(user["user_id"], user["phone_number"])
        
        # Store refresh token
        await db_auth_service.store_refresh_token(user["user_id"], tokens["refresh_token"])
        
        logger.info(f"Login successful for user {user['user_id']}")
        
        return AuthTokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=user["user_id"],
            phone_number=user["phone_number"],
            is_new_user=user.get("is_new_user", False),
            profile_exists=user.get("profile_exists", False),
            profile_completion_required=not user.get("profile_exists", False)
        )
        
    except APIException as e:
        logger.warning(f"API Exception in login: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred during login"
            ).dict()
        )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> AuthTokenResponse:
    """
    Refresh access token using refresh token.
    
    This endpoint generates a new access token using a valid refresh token.
    The refresh token must not be expired and must exist in the system.
    
    Args:
        request: Refresh token request containing the refresh token
        
    Returns:
        AuthTokenResponse with new access token and user information
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        logger.info("Token refresh attempt")
        
        # Verify refresh token
        user_info = db_auth_service.verify_refresh_token(request.refresh_token)
        
        # Generate new tokens
        tokens = db_auth_service.generate_tokens(user_info["user_id"], user_info["phone_number"])
        
        # Update refresh token in database
        await db_auth_service.store_refresh_token(user_info["user_id"], tokens["refresh_token"])
        
        logger.info(f"Token refresh successful for user {user_info['user_id']}")
        
        # Get user profile status for refresh token response
        profile_exists = False
        try:
            from src.services.user_profile_service import user_profile_service
            profile = await user_profile_service.get_user_profile_by_id(user_info["user_id"])
            profile_exists = profile is not None
        except Exception as e:
            logger.warning(f"Could not fetch user profile: {str(e)}")
            # Default to no profile if service is unavailable
        
        return AuthTokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=user_info["user_id"],
            phone_number=user_info["phone_number"],
            is_new_user=False,  # Refresh token means user already exists
            profile_exists=profile_exists,
            profile_completion_required=not profile_exists
        )
        
    except APIException as e:
        logger.warning(f"API Exception in refresh_token: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in refresh_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred during token refresh"
            ).dict()
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    request: LogoutRequest,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Logout user and invalidate refresh token.
    
    This endpoint logs out the user by invalidating their refresh token.
    You can provide either:
    1. Access token in Authorization header (to get user info)
    2. Refresh token in request body (to revoke directly)
    
    Args:
        request: Logout request (optional refresh token)
        credentials: HTTP Bearer token for authentication (access token)
        
    Returns:
        Dict with logout confirmation
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user_info = None
        
        # If refresh token is provided in request body, use it directly
        if request.refresh_token:
            logger.info("Logout using refresh token from request body")
            user_info = db_auth_service.verify_refresh_token(request.refresh_token)
        elif authorization:
            # Extract token from "Bearer <token>" format
            if authorization.startswith("Bearer "):
                token = authorization[7:]  # Remove "Bearer " prefix
                logger.info("Logout using access token from Authorization header")
                user_info = db_auth_service.verify_access_token(token)
            else:
                raise APIException(
                    message="Invalid authorization header format. Use 'Bearer <token>'",
                    error_code="INVALID_AUTH_HEADER",
                    status_code=401
                )
        else:
            raise APIException(
                message="Either refresh_token in request body or Authorization header is required",
                error_code="MISSING_AUTH",
                status_code=401
            )
        
        # Revoke refresh token
        if request.refresh_token:
            # Revoke the specific refresh token
            await db_auth_service.revoke_specific_refresh_token(request.refresh_token)
        else:
            # Revoke all refresh tokens for the user
            await db_auth_service.revoke_refresh_token(user_info['user_id'])
        
        logger.info(f"Logout successful for user {user_info['user_id']}")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except APIException as e:
        logger.warning(f"API Exception in logout: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred during logout"
            ).dict()
        )


@router.get("/profile", response_model=UserProfile)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Get user profile information.
    
    This endpoint returns the current user's profile information
    based on the provided access token.
    
    Args:
        credentials: HTTP Bearer token for authentication
        
    Returns:
        UserProfile with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify access token
        user_info = db_auth_service.verify_access_token(credentials.credentials)
        
        # Get user details from database
        from src.db.connection import aget_connection, release_connection
        conn = await aget_connection()
        try:
            query = """
                SELECT user_id, phone_number, is_verified, created_at, last_login
                FROM nal.users 
                WHERE user_id = $1
            """
            user_row = await conn.fetchrow(query, user_info["user_id"])
            
            if not user_row:
                raise APIException(
                    message="User not found.",
                    error_code="USER_NOT_FOUND",
                    status_code=404
                )
            
            return UserProfile(
                user_id=str(user_row["user_id"]),
                phone_number=user_row["phone_number"],
                is_verified=user_row["is_verified"],
                created_at=user_row["created_at"],
                last_login=user_row["last_login"]
            )
            
        finally:
            await release_connection(conn)
        
    except APIException as e:
        logger.warning(f"API Exception in get_profile: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred while fetching profile"
            ).dict()
        )


# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user.
    
    This can be used in other endpoints that require authentication.
    
    Args:
        credentials: HTTP Bearer token for authentication
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user_info = db_auth_service.verify_access_token(credentials.credentials)
        return user_info
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=AuthErrorResponse(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            ).dict()
        )
