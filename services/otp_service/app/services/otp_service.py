import json
import logging
from datetime import datetime
from typing import Optional, Tuple
from app.db.redis import RedisClient
from app.core.config import settings
from app.schemas.otp_schema import OTPData, OTPRequest
from app.utils.random_code import generate_otp

logger = logging.getLogger(__name__)

class OTPService:
    """Service for managing OTP operations with Redis"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    def _get_otp_key(self, payment_id: str) -> str:
        """Generate Redis key for OTP data"""
        return f"otp:{payment_id}"
    
    def _get_attempts_key(self, payment_id: str) -> str:
        """Generate Redis key for OTP attempts counter"""
        return f"otp_attempts:{payment_id}"
    
    def _get_lock_key(self, payment_id: str) -> str:
        """Generate Redis key for payment lock"""
        return f"otp_lock:{payment_id}"
    
    async def generate_otp(self, request: OTPRequest) -> Tuple[str, OTPData]:
        """
        Generate a new OTP for payment
        
        Args:
            request: OTP request data
        
        Returns:
            Tuple of (otp_code, otp_data)
        """
        # Check if payment is locked
        lock_key = self._get_lock_key(request.payment_id)
        if await self.redis.exists(lock_key):
            raise ValueError("Payment is locked due to too many failed attempts")
        
        # Generate OTP code
        otp_code = generate_otp(settings.OTP_LENGTH)
        
        # Create OTP data
        otp_data = OTPData(
            otp_code=otp_code,
            payment_id=request.payment_id,
            tuition_id=request.tuition_id,
            user_id=request.user_id,
            amount=request.amount,
            attempts=0,
            created_at=datetime.utcnow().isoformat(),
            email=request.email
        )
        
        # Store OTP in Redis with expiration
        otp_key = self._get_otp_key(request.payment_id)
        await self.redis.set(
            otp_key,
            otp_data.model_dump_json(),
            settings.OTP_EXPIRATION
        )
        
        # Initialize attempts counter
        attempts_key = self._get_attempts_key(request.payment_id)
        await self.redis.set(attempts_key, "0", settings.OTP_ATTEMPT_WINDOW)
        
        logger.info(f"Generated OTP for payment {request.payment_id}")
        return otp_code, otp_data
    
    async def verify_otp(self, payment_id: str, otp_code: str) -> Tuple[bool, str, int]:
        """
        Verify OTP code
        
        Args:
            payment_id: Payment ID
            otp_code: OTP code to verify
        
        Returns:
            Tuple of (is_valid, message, attempts_remaining)
        """
        # Check if payment is locked
        lock_key = self._get_lock_key(payment_id)
        if await self.redis.exists(lock_key):
            return False, "Payment is locked due to too many failed attempts", 0
        
        # Get OTP data
        otp_key = self._get_otp_key(payment_id)
        otp_data_json = await self.redis.get(otp_key)
        
        if not otp_data_json:
            return False, "OTP expired or not found", 0
        
        try:
            otp_data = OTPData.model_validate_json(otp_data_json)
        except Exception as e:
            logger.error(f"Failed to parse OTP data: {e}")
            return False, "Invalid OTP data", 0
        
        # Get current attempts
        attempts_key = self._get_attempts_key(payment_id)
        attempts = await self.redis.get(attempts_key)
        current_attempts = int(attempts) if attempts else 0
        
        # Verify OTP code
        if otp_data.otp_code == otp_code:
            # OTP is valid - clean up
            await self.redis.delete(otp_key)
            await self.redis.delete(attempts_key)
            logger.info(f"OTP verified successfully for payment {payment_id}")
            return True, "OTP verified successfully", settings.OTP_MAX_ATTEMPTS - current_attempts
        else:
            # Increment attempts
            current_attempts += 1
            await self.redis.set(attempts_key, str(current_attempts), settings.OTP_ATTEMPT_WINDOW)
            
            attempts_remaining = settings.OTP_MAX_ATTEMPTS - current_attempts
            
            # Lock payment if max attempts reached
            if current_attempts >= settings.OTP_MAX_ATTEMPTS:
                await self.redis.set(lock_key, "locked", settings.OTP_ATTEMPT_WINDOW)
                await self.redis.delete(otp_key)
                await self.redis.delete(attempts_key)
                logger.warning(f"Payment {payment_id} locked due to too many failed attempts")
                return False, "Maximum attempts reached. Payment is locked.", 0
            
            logger.warning(f"Invalid OTP for payment {payment_id}. Attempts: {current_attempts}/{settings.OTP_MAX_ATTEMPTS}")
            return False, f"Invalid OTP code. {attempts_remaining} attempts remaining.", attempts_remaining
    
    async def get_otp_data(self, payment_id: str) -> Optional[OTPData]:
        """
        Get OTP data for a payment
        
        Args:
            payment_id: Payment ID
        
        Returns:
            OTP data if exists, None otherwise
        """
        otp_key = self._get_otp_key(payment_id)
        otp_data_json = await self.redis.get(otp_key)
        
        if not otp_data_json:
            return None
        
        try:
            return OTPData.model_validate_json(otp_data_json)
        except Exception as e:
            logger.error(f"Failed to parse OTP data: {e}")
            return None
    
    async def get_remaining_time(self, payment_id: str) -> int:
        """
        Get remaining time for OTP in seconds
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Remaining time in seconds, -1 if OTP not found
        """
        otp_key = self._get_otp_key(payment_id)
        ttl = await self.redis.ttl(otp_key)
        return ttl if ttl > 0 else -1
    
    async def get_attempts_remaining(self, payment_id: str) -> int:
        """
        Get remaining verification attempts
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Number of remaining attempts
        """
        attempts_key = self._get_attempts_key(payment_id)
        attempts = await self.redis.get(attempts_key)
        current_attempts = int(attempts) if attempts else 0
        return max(0, settings.OTP_MAX_ATTEMPTS - current_attempts)
    
    async def is_payment_locked(self, payment_id: str) -> bool:
        """
        Check if payment is locked
        
        Args:
            payment_id: Payment ID
        
        Returns:
            True if locked, False otherwise
        """
        lock_key = self._get_lock_key(payment_id)
        return await self.redis.exists(lock_key)
    
    async def resend_otp(self, payment_id: str) -> Tuple[Optional[str], Optional[OTPData]]:
        """
        Resend OTP (delete old one and generate new)
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Tuple of (otp_code, otp_data) or (None, None) if OTP data not found
        """
        # Get existing OTP data
        otp_data = await self.get_otp_data(payment_id)
        
        if not otp_data:
            return None, None
        
        # Generate new OTP request from existing data
        request = OTPRequest(
            payment_id=payment_id,
            tuition_id=otp_data.tuition_id,
            user_id=otp_data.user_id,
            amount=otp_data.amount,
            email=otp_data.email
        )
        
        # Delete old OTP
        otp_key = self._get_otp_key(payment_id)
        await self.redis.delete(otp_key)
        
        # Generate new OTP
        return await self.generate_otp(request)
    
    async def delete_otp(self, payment_id: str):
        """
        Delete OTP and related data
        
        Args:
            payment_id: Payment ID
        """
        otp_key = self._get_otp_key(payment_id)
        attempts_key = self._get_attempts_key(payment_id)
        lock_key = self._get_lock_key(payment_id)
        
        await self.redis.delete(otp_key)
        await self.redis.delete(attempts_key)
        await self.redis.delete(lock_key)
        
        logger.info(f"Deleted OTP data for payment {payment_id}")
