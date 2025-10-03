import re
import phonenumbers
from typing import Optional, Dict, Any
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PhoneValidator:
    """Utility class for phone number validation and formatting."""
    
    @staticmethod
    def validate_phone_number(phone_number: str) -> Dict[str, Any]:
        """
        Validate and format phone number.
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            Dict with validation result and formatted number
            
        Raises:
            ValueError: If phone number is invalid
        """
        try:
            # Clean the phone number
            cleaned = re.sub(r'[^\d+]', '', phone_number)
            
            # Parse with phonenumbers library
            parsed = phonenumbers.parse(cleaned, None)
            
            # Validate the number
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            
            # Format in international format
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
            return {
                "valid": True,
                "formatted": formatted,
                "country_code": parsed.country_code,
                "national_number": parsed.national_number,
                "region": phonenumbers.region_code_for_number(parsed)
            }
            
        except phonenumbers.NumberParseException as e:
            logger.warning(f"Phone number parsing error: {str(e)}")
            raise ValueError(f"Invalid phone number format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error validating phone number: {str(e)}")
            raise ValueError("Failed to validate phone number")
    
    @staticmethod
    def is_valid_phone_number(phone_number: str) -> bool:
        """
        Check if phone number is valid without raising exceptions.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            True if valid, False otherwise
        """
        try:
            PhoneValidator.validate_phone_number(phone_number)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def format_phone_number(phone_number: str) -> Optional[str]:
        """
        Format phone number to international format.
        
        Args:
            phone_number: Phone number to format
            
        Returns:
            Formatted phone number or None if invalid
        """
        try:
            result = PhoneValidator.validate_phone_number(phone_number)
            return result["formatted"]
        except ValueError:
            return None
    
    @staticmethod
    def mask_phone_number(phone_number: str) -> str:
        """
        Mask phone number for logging purposes.
        
        Args:
            phone_number: Phone number to mask
            
        Returns:
            Masked phone number (e.g., +1234***7890)
        """
        try:
            if len(phone_number) < 8:
                return "***"
            
            # Keep first 4 and last 4 characters
            return phone_number[:4] + "*" * (len(phone_number) - 8) + phone_number[-4:]
        except Exception:
            return "***"


class TokenUtils:
    """Utility class for JWT token operations."""
    
    @staticmethod
    def extract_token_from_header(authorization_header: str) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            authorization_header: Authorization header value
            
        Returns:
            JWT token or None if invalid format
        """
        try:
            if not authorization_header:
                return None
            
            parts = authorization_header.split(" ", 1)
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return None
            
            return parts[1]
        except Exception:
            return None
    
    @staticmethod
    def is_token_expired(token: str, secret: str) -> bool:
        """
        Check if JWT token is expired without raising exceptions.
        
        Args:
            token: JWT token to check
            secret: JWT secret key
            
        Returns:
            True if expired, False otherwise
        """
        try:
            import jwt
            jwt.decode(token, secret, algorithms=["HS256"])
            return False
        except jwt.ExpiredSignatureError:
            return True
        except Exception:
            return True


class RateLimitUtils:
    """Utility class for rate limiting operations."""
    
    @staticmethod
    def get_rate_limit_key(phone_number: str, operation: str) -> str:
        """
        Generate rate limit key for Redis.
        
        Args:
            phone_number: Phone number
            operation: Operation type (e.g., 'otp', 'login')
            
        Returns:
            Rate limit key
        """
        import hashlib
        hashed_phone = hashlib.sha256(phone_number.encode()).hexdigest()[:16]
        return f"rate_limit:{operation}:{hashed_phone}"
    
    @staticmethod
    def get_otp_key(phone_number: str) -> str:
        """
        Generate OTP storage key for Redis.
        
        Args:
            phone_number: Phone number
            
        Returns:
            OTP key
        """
        import hashlib
        hashed_phone = hashlib.sha256(phone_number.encode()).hexdigest()
        return f"otp:{hashed_phone}"
    
    @staticmethod
    def get_refresh_token_key(user_id: str) -> str:
        """
        Generate refresh token storage key for Redis.
        
        Args:
            user_id: User ID
            
        Returns:
            Refresh token key
        """
        return f"refresh_token:{user_id}"


class SecurityUtils:
    """Utility class for security-related operations."""
    
    @staticmethod
    def generate_secure_random_string(length: int = 32) -> str:
        """
        Generate a secure random string.
        
        Args:
            length: Length of the string
            
        Returns:
            Secure random string
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        import bcrypt
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        import bcrypt
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def sanitize_phone_number(phone_number: str) -> str:
        """
        Sanitize phone number for storage.
        
        Args:
            phone_number: Phone number to sanitize
            
        Returns:
            Sanitized phone number
        """
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned
