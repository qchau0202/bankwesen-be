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
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    def _getOtpKey(self, payment_id: str) -> str:
        return f"otp:{payment_id}"
    
    def _getAttemptsKey(self, payment_id: str) -> str:
        return f"otp:attempts:{payment_id}"
    
    def _getLockKey(self, payment_id: str) -> str:
        return f"otp:lock:{payment_id}"
    
    async def generateOtpAsync(self, request: OTPRequest) -> Tuple[str, OTPData]:
        # Check if payment is locked
        lock_key = self._getLockKey(request.payment_id)
        if await self.redis.exists(lock_key):
            raise ValueError("Payment is locked due to too many failed attempts")
        
        # Generate OTP code
        otp_code = generate_otp(settings.OTP_LENGTH)
        
        # Create OTP data
        otp_data = OTPData(
            otp_code=otp_code,
            payment_id=request.payment_id,
            tuition_ids=request.tuition_ids,
            user_id=request.user_id,
            amount=request.amount,
            attempts=request.attempts,
            created_at=datetime.utcnow().isoformat(),
            email=request.email
        )
        
        # Store OTP in Redis with expiration
        otp_key = self._getOtpKey(request.payment_id)
        await self.redis.set(
            otp_key,
            otp_data.model_dump_json(),
            settings.OTP_EXPIRATION
        )
        
        # Initialize attempts counter
        attempts_key = self._getAttemptsKey(request.payment_id)
        await self.redis.set(attempts_key, "0", settings.OTP_ATTEMPT_WINDOW)
        
        logger.info(f"Generated OTP for payment {request.payment_id}")
        return otp_code, otp_data
    
    async def verifyOtpAsync(self, payment_id: str, otp_code: str) -> Tuple[bool, str, int]:
        logger.info(f"Verifying OTP: payment_id={payment_id}, code={otp_code}")
        
        # Check if payment is locked
        lock_key = self._getLockKey(payment_id)
        if await self.redis.exists(lock_key):
            logger.warning(f"Payment {payment_id} is locked")
            return False, "Payment is locked due to too many failed attempts", 0
        
        # Get OTP data
        otp_key = self._getOtpKey(payment_id)
        logger.info(f"Looking for OTP in Redis with key: {otp_key}")
        otp_data_json = await self.redis.get(otp_key)
        
        if not otp_data_json:
            logger.warning(f"OTP not found in Redis for key: {otp_key}")
            # Check if there are any OTP keys to help debug
            all_otp_keys = []
            try:
                cursor = 0
                while True:
                    cursor, keys = await self.redis.redis.scan(cursor, match="otp:*", count=100)
                    all_otp_keys.extend([k.decode() if isinstance(k, bytes) else k for k in keys])
                    if cursor == 0:
                        break
                if all_otp_keys:
                    logger.info(f"Available OTP keys in Redis: {all_otp_keys}")
                else:
                    logger.info("No OTP keys found in Redis")
            except Exception as e:
                logger.error(f"Error checking Redis keys: {e}")
            
            return False, "OTP expired or not found", 0
        
        try:
            otp_data = OTPData.model_validate_json(otp_data_json)
        except Exception as e:
            logger.error(f"Failed to parse OTP data: {e}")
            return False, "Invalid OTP data", 0
        
        # Get current attempts
        attempts_key = self._getAttemptsKey(payment_id)
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
    
    async def getOtpDataAsync(self, payment_id: str) -> Optional[OTPData]:
        otp_key = self._getOtpKey(payment_id)
        otp_data_json = await self.redis.get(otp_key)
        
        if not otp_data_json:
            return None
        
        try:
            return OTPData.model_validate_json(otp_data_json)
        except Exception as e:
            logger.error(f"Failed to parse OTP data: {e}")
            return None
    
    async def getRemainingTimeAsync(self, payment_id: str) -> int:
        otp_key = self._getOtpKey(payment_id)
        ttl = await self.redis.ttl(otp_key)
        return ttl if ttl > 0 else -1
    
    async def getAttemptsRemainingAsync(self, payment_id: str) -> int:
        attempts_key = self._getAttemptsKey(payment_id)
        attempts = await self.redis.get(attempts_key)
        current_attempts = int(attempts) if attempts else 0
        return max(0, settings.OTP_MAX_ATTEMPTS - current_attempts)
    
    async def isPaymentLockedAsync(self, payment_id: str) -> bool:
        lock_key = self._getLockKey(payment_id)
        return await self.redis.exists(lock_key)
    
    async def deleteOtpAsync(self, payment_id: str):
        otp_key = self._getOtpKey(payment_id)
        attempts_key = self._getAttemptsKey(payment_id)
        lock_key = self._getLockKey(payment_id)
        
        await self.redis.delete(otp_key)
        await self.redis.delete(attempts_key)
        await self.redis.delete(lock_key)
        
        logger.info(f"Deleted OTP data for payment {payment_id}")