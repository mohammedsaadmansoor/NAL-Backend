import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
from src.settings import settings
from src.services.redis_service import redis_service
from src.db.connection import aget_connection, release_connection
from src.utils.logging import get_logger
from src.services.utils.exceptions import APIException

logger = get_logger(__name__)


class AuthService:
    """Authentication service for mobile number-based authentication."""
    
    def __init__(self):
        self.jwt_secret = settings.jwt_secret if hasattr(settings, 'jwt_secret') else "your-secret-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.otp_expire_minutes = 5
        self.otp_length = 6
        self.max_otp_attempts = 3
        self.otp_cooldown_minutes = 1
    
    def generate_otp(self) -> str:
        """Generate a random OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])
    
    def hash_phone_number(self, phone_number: str) -> str:
        """Hash phone number for storage."""
        return hashlib.sha256(phone_number.encode()).hexdigest()
    
    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """
        Send OTP to phone number with rate limiting.
        
        Args:
            phone_number: Phone number in international format
            
        Returns:
            Dict with success status and message
        """
        try:
            # Check rate limiting
            rate_limit_key = f"otp_rate_limit:{phone_number}"
            can_send = await redis_service.send_email_with_counter(rate_limit_key, phone_number)
            
            if not can_send:
                raise APIException(
                    message="Too many OTP requests. Please wait before requesting another OTP.",
                    error_code="RATE_LIMIT_EXCEEDED",
                    status_code=429
                )
            
            # Generate OTP
            otp_code = self.generate_otp()
            hashed_phone = self.hash_phone_number(phone_number)
            
            # Store OTP in Redis with expiry
            otp_key = f"otp:{hashed_phone}"
            otp_data = {
                "code": otp_code,
                "phone_number": phone_number,
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0
            }
            
            # Store OTP for 5 minutes
            await redis_service.get_redis_client()
            redis_client = await redis_service.get_redis_client()
            await redis_client.setex(
                otp_key, 
                self.otp_expire_minutes * 60, 
                str(otp_data)
            )
            
            # Send OTP via SMS service
            from src.services.sms_service import get_sms_service
            sms_service = get_sms_service()
            sms_result = await sms_service.send_otp(phone_number, otp_code)
            
            if not sms_result.get("success", False):
                logger.error(f"Failed to send SMS: {sms_result.get('message', 'Unknown error')}")
                # Don't fail the request, but log the error
                # In production, you might want to fail here
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_in": self.otp_expire_minutes * 60,
                "retry_after": self.otp_cooldown_minutes * 60
            }
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            raise APIException(
                message="Failed to send OTP. Please try again.",
                error_code="OTP_SEND_FAILED",
                status_code=500
            )
    
    async def verify_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP code for phone number.
        
        Args:
            phone_number: Phone number in international format
            otp_code: OTP code to verify
            
        Returns:
            Dict with verification result
        """
        try:
            hashed_phone = self.hash_phone_number(phone_number)
            otp_key = f"otp:{hashed_phone}"
            
            # Get OTP from Redis
            redis_client = await redis_service.get_redis_client()
            otp_data_str = await redis_client.get(otp_key)
            
            if not otp_data_str:
                raise APIException(
                    message="OTP expired or not found. Please request a new OTP.",
                    error_code="OTP_EXPIRED",
                    status_code=400
                )
            
            # Parse OTP data
            import ast
            otp_data = ast.literal_eval(otp_data_str)
            
            # Check attempts
            if otp_data.get("attempts", 0) >= self.max_otp_attempts:
                # Delete OTP after max attempts
                await redis_client.delete(otp_key)
                raise APIException(
                    message="Maximum OTP attempts exceeded. Please request a new OTP.",
                    error_code="MAX_ATTEMPTS_EXCEEDED",
                    status_code=400
                )
            
            # Verify OTP
            if otp_data["code"] != otp_code:
                # Increment attempts
                otp_data["attempts"] += 1
                await redis_client.setex(
                    otp_key,
                    self.otp_expire_minutes * 60,
                    str(otp_data)
                )
                
                remaining_attempts = self.max_otp_attempts - otp_data["attempts"]
                raise APIException(
                    message=f"Invalid OTP. {remaining_attempts} attempts remaining.",
                    error_code="INVALID_OTP",
                    status_code=400
                )
            
            # OTP verified successfully
            # Delete OTP from Redis
            await redis_client.delete(otp_key)
            
            return {
                "success": True,
                "message": "OTP verified successfully",
                "phone_number": phone_number
            }
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            raise APIException(
                message="Failed to verify OTP. Please try again.",
                error_code="OTP_VERIFICATION_FAILED",
                status_code=500
            )
    
    async def create_or_get_user(self, phone_number: str) -> Dict[str, Any]:
        """
        Create or get user by phone number.
        
        Args:
            phone_number: Phone number in international format
            
        Returns:
            Dict with user information
        """
        try:
            conn = await aget_connection()
            try:
                # Check if user exists
                user_query = """
                    SELECT user_id, phone_number, is_verified, created_at, last_login
                    FROM users 
                    WHERE phone_number = $1
                """
                user_row = await conn.fetchrow(user_query, phone_number)
                
                if user_row:
                    # Update last login
                    update_query = """
                        UPDATE users 
                        SET last_login = $1 
                        WHERE phone_number = $2
                    """
                    await conn.execute(update_query, datetime.utcnow(), phone_number)
                    
                    # Check if user has a profile
                    profile_query = """
                        SELECT user_id FROM user_profiles WHERE user_id = $1
                    """
                    profile_exists = await conn.fetchrow(profile_query, user_row["user_id"])
                    
                    return {
                        "user_id": str(user_row["user_id"]),
                        "phone_number": user_row["phone_number"],
                        "is_verified": user_row["is_verified"],
                        "created_at": user_row["created_at"],
                        "last_login": datetime.utcnow(),
                        "profile_exists": profile_exists is not None,
                        "is_new_user": False
                    }
                else:
                    # Create new user
                    import uuid
                    user_id = str(uuid.uuid4())
                    
                    insert_query = """
                        INSERT INTO users (user_id, phone_number, is_verified, created_at, last_login)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING user_id, phone_number, is_verified, created_at, last_login
                    """
                    user_row = await conn.fetchrow(
                        insert_query,
                        user_id,
                        phone_number,
                        True,  # Mark as verified since OTP was verified
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                    
                    logger.info(f"New user created: {user_id}")
                    
                    return {
                        "user_id": str(user_row["user_id"]),
                        "phone_number": user_row["phone_number"],
                        "is_verified": user_row["is_verified"],
                        "created_at": user_row["created_at"],
                        "last_login": user_row["last_login"],
                        "profile_exists": False,
                        "is_new_user": True
                    }
                    
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"Error creating/getting user: {str(e)}")
            raise APIException(
                message="Failed to create user account. Please try again.",
                error_code="USER_CREATION_FAILED",
                status_code=500
            )
    
    def generate_tokens(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Generate JWT access and refresh tokens.
        
        Args:
            user_id: User ID
            phone_number: User's phone number
            
        Returns:
            Dict with tokens and expiry information
        """
        try:
            now = datetime.utcnow()
            
            # Access token payload
            access_payload = {
                "sub": user_id,
                "phone_number": phone_number,
                "type": "access",
                "iat": now,
                "exp": now + timedelta(minutes=self.access_token_expire_minutes)
            }
            
            # Refresh token payload
            refresh_payload = {
                "sub": user_id,
                "phone_number": phone_number,
                "type": "refresh",
                "iat": now,
                "exp": now + timedelta(days=self.refresh_token_expire_days)
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": self.access_token_expire_minutes * 60,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error generating tokens: {str(e)}")
            raise APIException(
                message="Failed to generate authentication tokens.",
                error_code="TOKEN_GENERATION_FAILED",
                status_code=500
            )
    
    async def store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """Store refresh token in Redis."""
        try:
            redis_client = await redis_service.get_redis_client()
            token_key = f"refresh_token:{user_id}"
            await redis_client.setex(
                token_key,
                self.refresh_token_expire_days * 24 * 60 * 60,
                refresh_token
            )
        except Exception as e:
            logger.error(f"Error storing refresh token: {str(e)}")
    
    async def verify_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Verify refresh token and return user information.
        
        Args:
            refresh_token: Refresh token to verify
            
        Returns:
            Dict with user information
        """
        try:
            # Decode token
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            if payload.get("type") != "refresh":
                raise APIException(
                    message="Invalid token type.",
                    error_code="INVALID_TOKEN_TYPE",
                    status_code=401
                )
            
            user_id = payload.get("sub")
            phone_number = payload.get("phone_number")
            
            # Check if token exists in Redis
            redis_client = await redis_service.get_redis_client()
            token_key = f"refresh_token:{user_id}"
            stored_token = await redis_client.get(token_key)
            
            if not stored_token or stored_token != refresh_token:
                raise APIException(
                    message="Invalid or expired refresh token.",
                    error_code="INVALID_REFRESH_TOKEN",
                    status_code=401
                )
            
            return {
                "user_id": user_id,
                "phone_number": phone_number
            }
            
        except jwt.ExpiredSignatureError:
            raise APIException(
                message="Refresh token has expired.",
                error_code="REFRESH_TOKEN_EXPIRED",
                status_code=401
            )
        except jwt.InvalidTokenError:
            raise APIException(
                message="Invalid refresh token.",
                error_code="INVALID_REFRESH_TOKEN",
                status_code=401
            )
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error verifying refresh token: {str(e)}")
            raise APIException(
                message="Failed to verify refresh token.",
                error_code="TOKEN_VERIFICATION_FAILED",
                status_code=500
            )
    
    async def revoke_refresh_token(self, user_id: str) -> None:
        """Revoke refresh token by deleting it from Redis."""
        try:
            redis_client = await redis_service.get_redis_client()
            token_key = f"refresh_token:{user_id}"
            await redis_client.delete(token_key)
        except Exception as e:
            logger.error(f"Error revoking refresh token: {str(e)}")
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify access token and return user information.
        
        Args:
            token: Access token to verify
            
        Returns:
            Dict with user information
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            if payload.get("type") != "access":
                raise APIException(
                    message="Invalid token type.",
                    error_code="INVALID_TOKEN_TYPE",
                    status_code=401
                )
            
            return {
                "user_id": payload.get("sub"),
                "phone_number": payload.get("phone_number")
            }
            
        except jwt.ExpiredSignatureError:
            raise APIException(
                message="Access token has expired.",
                error_code="ACCESS_TOKEN_EXPIRED",
                status_code=401
            )
        except jwt.InvalidTokenError:
            raise APIException(
                message="Invalid access token.",
                error_code="INVALID_ACCESS_TOKEN",
                status_code=401
            )
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error verifying access token: {str(e)}")
            raise APIException(
                message="Failed to verify access token.",
                error_code="TOKEN_VERIFICATION_FAILED",
                status_code=500
            )


# Global auth service instance
auth_service = AuthService()
