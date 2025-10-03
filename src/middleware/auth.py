from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.services.auth_service import auth_service
from src.services.utils.exceptions import APIException
from src.utils.logging import get_logger
from typing import List, Optional

logger = get_logger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT Authentication middleware for protecting routes."""
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/api/docs",
            "/api/redoc", 
            "/api/openapi.json",
            "/api/azure/health",
            "/api/auth/send-otp",
            "/api/auth/verify-otp",
            "/api/auth/login"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check authentication."""
        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return self._unauthorized_response("Authorization header missing")
        
        # Extract token
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return self._unauthorized_response("Invalid authorization scheme")
        except ValueError:
            return self._unauthorized_response("Invalid authorization header format")
        
        # Verify token
        try:
            user_info = auth_service.verify_access_token(token)
            
            # Add user info to request state
            request.state.user_id = user_info["user_id"]
            request.state.phone_number = user_info["phone_number"]
            request.state.authenticated = True
            
            logger.debug(f"User {user_info['user_id']} authenticated successfully")
            
        except APIException as e:
            logger.warning(f"Authentication failed: {e.message}")
            return self._unauthorized_response(e.message, e.error_code)
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            return self._unauthorized_response("Authentication failed")
        
        # Continue with the request
        response = await call_next(request)
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from authentication."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _unauthorized_response(self, message: str, error_code: str = "UNAUTHORIZED") -> JSONResponse:
        """Return unauthorized response."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error_code": error_code,
                "message": message,
                "details": None
            }
        )


class OptionalJWTAuthMiddleware(BaseHTTPMiddleware):
    """Optional JWT Authentication middleware that doesn't require authentication."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with optional authentication."""
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        
        if authorization:
            try:
                scheme, token = authorization.split(" ", 1)
                if scheme.lower() == "bearer":
                    # Verify token
                    user_info = auth_service.verify_access_token(token)
                    
                    # Add user info to request state
                    request.state.user_id = user_info["user_id"]
                    request.state.phone_number = user_info["phone_number"]
                    request.state.authenticated = True
                    
                    logger.debug(f"User {user_info['user_id']} authenticated successfully")
                    
            except (APIException, ValueError) as e:
                # Log but don't fail the request
                logger.debug(f"Optional authentication failed: {str(e)}")
                request.state.authenticated = False
        else:
            request.state.authenticated = False
        
        # Continue with the request
        response = await call_next(request)
        return response


def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state."""
    if not hasattr(request.state, 'user_id') or not request.state.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.user_id


def get_current_phone_number(request: Request) -> str:
    """Get current user phone number from request state."""
    if not hasattr(request.state, 'phone_number') or not request.state.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.phone_number


def is_authenticated(request: Request) -> bool:
    """Check if user is authenticated."""
    return hasattr(request.state, 'authenticated') and request.state.authenticated
