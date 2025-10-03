import redis.asyncio as redis
from typing import Optional
from src.settings import settings
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for handling email sending with counter and expiry functionality."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = None
        self.connection_pool = None
        
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling."""
        if self.redis_client is None:
            # Build Redis URL
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            else:
                redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            
            # For Azure Redis Cache, use SSL
            if settings.redis_host.lower() == "cache.windows.net" or settings.redis_host.lower().endswith(".cache.windows.net"):
                if settings.redis_password:
                    redis_url = f"rediss://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}?ssl_cert_reqs=none"
                else:
                    redis_url = f"rediss://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}?ssl_cert_reqs=none"
            
            self.connection_pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=10
            )
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
        
        return self.redis_client
    
    async def send_email_with_counter(self, email_key: str, to_email: str) -> bool:
        """
        Send email using Redis counter with 15-minute expiry.
        
        Args:
            email_key: Unique key for the email counter (e.g., user_id or session_id)
            to_email: Email address to send to
            email_data: Additional email data (optional)
            
        Returns:
            bool: True if email should be sent (counter == 1), False otherwise
        """
        try:
            redis_client = await self.get_redis_client()
            
            # Create the counter key
            counter_key = f"send_email:{email_key}"
            
            # Increment the counter
            current_count = await redis_client.incr(counter_key)
            
            # Set expiry to 15 minutes (900 seconds) if this is the first increment
            if current_count == 1:
                await redis_client.expire(counter_key, 900)  # 15 minutes
                logger.info(f"Email counter created for key {email_key} with 15-minute expiry")
            
            # Only send email if counter is 1 (first time in 15 minutes)
            if current_count == 1:
                logger.info(f"Sending email to {to_email} for key {email_key} (counter: {current_count})")
                return True
            else:
                logger.info(f"Email not sent to {to_email} for key {email_key} (counter: {current_count}) - within 15-minute window")
                return False
                
        except Exception as e:
            logger.error(f"Error in send_email_with_counter: {str(e)}")
            return False
    
    async def get_email_counter(self, email_key: str) -> Optional[int]:
        """Get the current email counter value for a given key."""
        try:
            redis_client = await self.get_redis_client()
            counter_key = f"send_email:{email_key}"
            value = await redis_client.get(counter_key)
            return int(value) if value else None
        except Exception as e:
            logger.error(f"Error getting email counter: {str(e)}")
            return None
    
    async def reset_email_counter(self, email_key: str) -> bool:
        """Reset the email counter for a given key."""
        try:
            redis_client = await self.get_redis_client()
            counter_key = f"send_email:{email_key}"
            result = await redis_client.delete(counter_key)
            logger.info(f"Email counter reset for key {email_key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error resetting email counter: {str(e)}")
            return False
    
    async def get_counter_ttl(self, email_key: str) -> Optional[int]:
        """Get the remaining TTL (time to live) for a counter key."""
        try:
            redis_client = await self.get_redis_client()
            counter_key = f"send_email:{email_key}"
            ttl = await redis_client.ttl(counter_key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting counter TTL: {str(e)}")
            return None
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()

# Global Redis service instance
redis_service = RedisService() 