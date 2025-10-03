import aiohttp
import asyncio
from src.settings import settings
from src.services.redis_service import redis_service
import logging

logger = logging.getLogger(__name__)

class MailService:
   def __init__(self):
       self.email_endpoint=settings.email_api_endpoint
       self.email_endpoint_2=settings.email_api_endpoint_2
       self.headers = {
            "Content-Type": "application/json"
        }
   
   async def send_mail(self, to: str):
        payload = {
            "to": to
        }
        async with aiohttp.ClientSession() as session:
         async with session.post(self.email_endpoint, json=payload, headers=self.headers) as response:
            if response.ok:
                print(f"Email request successfully sent! Status Code: {response.status}")
            else:
                print(f"Failed to send email request. Status Code: {response.status}")
                print("Response Body:", await response.text())
                
   async def send_mail_2(self, to: str):
        payload = {
            "to": to
        }
        async with aiohttp.ClientSession() as session:
         async with session.post(self.email_endpoint_2, json=payload, headers=self.headers) as response:
            if response.ok:
                print(f"Email request successfully sent! Status Code: {response.status}")
            else:
                print(f"Failed to send email request. Status Code: {response.status}")
                print("Response Body:", await response.text())

   async def send_mail_with_redis_counter(self, email_key: str, to: str, email_data: dict = None) -> bool:
        """Send email using Redis counter with 15-minute expiry."""
        try:
            should_send = await redis_service.send_email_with_counter(email_key, to, email_data)
            
            if should_send:
                await self.send_mail(to)
                logger.info(f"Email sent to {to} with Redis counter key {email_key}")
                return True
            else:
                logger.info(f"Email not sent to {to} - within 15-minute window for key {email_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error in send_mail_with_redis_counter: {str(e)}")
            return False

   async def send_mail_2_with_redis_counter(self, email_key: str, to: str, email_data: dict = None) -> bool:
        """Send email using second endpoint with Redis counter and 15-minute expiry."""
        try:
            should_send = await redis_service.send_email_with_counter(email_key, to, email_data)
            
            if should_send:
                await self.send_mail_2(to)
                logger.info(f"Email sent to {to} via endpoint 2 with Redis counter key {email_key}")
                return True
            else:
                logger.info(f"Email not sent to {to} via endpoint 2 - within 15-minute window for key {email_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error in send_mail_2_with_redis_counter: {str(e)}")
            return False

   async def get_email_counter_status(self, email_key: str) -> dict:
        """Get the current email counter status for a given key."""
        try:
            counter_value = await redis_service.get_email_counter(email_key)
            ttl = await redis_service.get_counter_ttl(email_key)
            
            return {
                "email_key": email_key,
                "counter_value": counter_value,
                "ttl_seconds": ttl,
                "can_send_email": counter_value is None or counter_value == 0
            }
        except Exception as e:
            logger.error(f"Error getting email counter status: {str(e)}")
            return {
                "email_key": email_key,
                "counter_value": None,
                "ttl_seconds": None,
                "can_send_email": False,
                "error": str(e)
            }

   async def reset_email_counter(self, email_key: str) -> bool:
        """Reset the email counter for a given key."""
        return await redis_service.reset_email_counter(email_key)

# LOGIC_APP_URL ="https://kms-logic-app-prod.azurewebsites.net:443/api/testing-mail/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=I1SF3aUxxzcCE6Gk7hoPRRc9JvY_uDqV4IBhCF4h8iU"


# payload = {
#     "to": "gourav.kumar@tredence.com",
#     "cc":"aakash.tandale@tredence.com"
# }
# headers = {
#     "Content-Type": "application/json"
# }
# response = requests.post(LOGIC_APP_URL, json=payload, headers=headers)


# if response.ok:
#     print(f"Email request successfully sent! Status Code: {response.status_code}")
# else:
#     print(f"Failed to send email request. Status Code: {response.status_code}")
#     print("Response Body:", response.text)