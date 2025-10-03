from abc import ABC, abstractmethod
from typing import Dict, Any
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SMSServiceInterface(ABC):
    """Abstract base class for SMS service implementations."""
    
    @abstractmethod
    async def send_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Send OTP via SMS.
        
        Args:
            phone_number: Phone number in international format
            otp_code: OTP code to send
            
        Returns:
            Dict with sending result
        """
        pass


class MockSMSService(SMSServiceInterface):
    """Mock SMS service for development and testing."""
    
    async def send_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Mock OTP sending - just logs the OTP.
        
        Args:
            phone_number: Phone number in international format
            otp_code: OTP code to send
            
        Returns:
            Dict with sending result
        """
        logger.info(f"[MOCK SMS] Sending OTP {otp_code} to {phone_number}")
        
        # Simulate some processing time
        import asyncio
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "OTP sent successfully (mock)",
            "provider": "mock",
            "message_id": f"mock_{phone_number}_{otp_code}"
        }


class TwilioSMSService(SMSServiceInterface):
    """Twilio SMS service implementation."""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
    
    async def send_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Send OTP via Twilio SMS.
        
        Args:
            phone_number: Phone number in international format
            otp_code: OTP code to send
            
        Returns:
            Dict with sending result
        """
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            message = client.messages.create(
                body=f"Your OTP code is: {otp_code}. This code will expire in 5 minutes.",
                from_=self.from_number,
                to=phone_number
            )
            
            logger.info(f"OTP sent via Twilio to {phone_number}, SID: {message.sid}")
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "provider": "twilio",
                "message_id": message.sid
            }
            
        except Exception as e:
            logger.error(f"Failed to send OTP via Twilio: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send OTP: {str(e)}",
                "provider": "twilio",
                "error": str(e)
            }


class AWSSNSService(SMSServiceInterface):
    """AWS SNS SMS service implementation."""
    
    def __init__(self, region_name: str, access_key_id: str = None, secret_access_key: str = None):
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
    
    async def send_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Send OTP via AWS SNS SMS.
        
        Args:
            phone_number: Phone number in international format
            otp_code: OTP code to send
            
        Returns:
            Dict with sending result
        """
        try:
            import boto3
            
            # Create SNS client
            if self.access_key_id and self.secret_access_key:
                sns = boto3.client(
                    'sns',
                    region_name=self.region_name,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key
                )
            else:
                # Use default credentials (IAM role, environment variables, etc.)
                sns = boto3.client('sns', region_name=self.region_name)
            
            # Send SMS
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=f"Your OTP code is: {otp_code}. This code will expire in 5 minutes."
            )
            
            logger.info(f"OTP sent via AWS SNS to {phone_number}, MessageId: {response['MessageId']}")
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "provider": "aws_sns",
                "message_id": response['MessageId']
            }
            
        except Exception as e:
            logger.error(f"Failed to send OTP via AWS SNS: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send OTP: {str(e)}",
                "provider": "aws_sns",
                "error": str(e)
            }


class SMSServiceFactory:
    """Factory class for creating SMS service instances."""
    
    @staticmethod
    def create_sms_service(provider: str, **kwargs) -> SMSServiceInterface:
        """
        Create SMS service instance based on provider.
        
        Args:
            provider: SMS provider ('mock', 'twilio', 'aws_sns')
            **kwargs: Provider-specific configuration
            
        Returns:
            SMS service instance
        """
        if provider.lower() == 'mock':
            return MockSMSService()
        elif provider.lower() == 'twilio':
            return TwilioSMSService(
                account_sid=kwargs.get('account_sid'),
                auth_token=kwargs.get('auth_token'),
                from_number=kwargs.get('from_number')
            )
        elif provider.lower() == 'aws_sns':
            return AWSSNSService(
                region_name=kwargs.get('region_name'),
                access_key_id=kwargs.get('access_key_id'),
                secret_access_key=kwargs.get('secret_access_key')
            )
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")


# Global SMS service instance (will be initialized based on configuration)
sms_service: SMSServiceInterface = None


def get_sms_service() -> SMSServiceInterface:
    """Get the global SMS service instance."""
    global sms_service
    if sms_service is None:
        # Default to mock service
        sms_service = MockSMSService()
    return sms_service


def initialize_sms_service(provider: str, **kwargs) -> None:
    """Initialize the global SMS service."""
    global sms_service
    sms_service = SMSServiceFactory.create_sms_service(provider, **kwargs)
    logger.info(f"SMS service initialized with provider: {provider}")
