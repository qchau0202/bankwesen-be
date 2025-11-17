from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.otp_schema import (
    OTPRequest,
    OTPVerifyRequest,
    OTPResponse,
    OTPVerifyResponse
)
from app.services.otp_service import OTPService
from app.db.redis import RedisClient, get_redis
from app.core.config import settings
from app.core.security import verify_api_key
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/otp", tags=["OTP"], dependencies=[Depends(verify_api_key)])

async def get_otp_service(redis_client: RedisClient = Depends(get_redis)) -> OTPService:
    return OTPService(redis_client)

@router.post("/request", response_model=OTPResponse, status_code=status.HTTP_201_CREATED)
async def request_otp(
    request: OTPRequest,
    otp_service: OTPService = Depends(get_otp_service)
):
    try:
        logger.info(f"Received OTP request for payment_id={request.payment_id}, email={request.email}")
        
        # Check if payment is locked
        is_locked = await otp_service.isPaymentLockedAsync(request.payment_id)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to too many failed attempts. Please try again later."
            )
        
        # Generate OTP
        otp_code, otp_data = await otp_service.generateOtpAsync(request)
        
        # Get expiration time
        expires_in = await otp_service.getRemainingTimeAsync(request.payment_id)
        attempts_remaining = await otp_service.getAttemptsRemainingAsync(request.payment_id)
        
        # Send OTP via email using notification service
        if request.email:
            try:
                notification_url = f"{settings.NOTIFICATION_SERVICE_URL}/api/notification/email-otp"
                logger.info(f"Sending OTP email to {request.email} via {notification_url}")
                
                async with httpx.AsyncClient() as client:
                    notification_response = await client.post(
                        notification_url,
                        json={
                            "email": request.email,
                            "otp_code": otp_code,
                            "expires_in": expires_in,
                            "payment_id": request.payment_id,
                            "amount": request.amount
                        },
                        headers={settings.API_KEY_NAME: settings.API_KEY},
                        timeout=10.0
                    )
                    
                    if notification_response.status_code != 200:
                        logger.warning(f"Failed to send OTP email: {notification_response.text}")
                        logger.info(f"OTP for payment {request.payment_id}: {otp_code}")
                    else:
                        logger.info(f"OTP email sent successfully to {request.email}")
                        logger.info(f"OTP CODE for payment {request.payment_id}: {otp_code}")
            except Exception as e:
                logger.error(f"Error sending OTP email: {e}")
                logger.info(f"OTP for payment {request.payment_id}: {otp_code}")
        else:
            logger.info(f"OTP CODE for payment {request.payment_id}: {otp_code}")
        
        return OTPResponse(
            success=True,
            message="OTP generated successfully. Check your email.",
            payment_id=request.payment_id,
            expires_in=expires_in,
            attempts_remaining=attempts_remaining
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP"
        )

@router.post("/verify", response_model=OTPVerifyResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    otp_service: OTPService = Depends(get_otp_service)
):
    try:
        logger.info(f"Verifying OTP for payment_id={request.payment_id}, code={request.otp_code}")
        
        is_valid, message, attempts_remaining = await otp_service.verifyOtpAsync(
            request.payment_id,
            request.otp_code
        )
        
        logger.info(f"OTP verification result: valid={is_valid}, message={message}, attempts_remaining={attempts_remaining}")
        
        if is_valid:
            return OTPVerifyResponse(
                success=True,
                message=message,
                payment_id=request.payment_id,
                verified=True,
                attempts_remaining=None,
                locked=False
            )
        else:
            # Check if payment is now locked
            is_locked = await otp_service.isPaymentLockedAsync(request.payment_id)
            
            if is_locked:
                return OTPVerifyResponse(
                    success=False,
                    message=message,
                    payment_id=request.payment_id,
                    verified=False,
                    attempts_remaining=0,
                    locked=True
                )
            else:
                return OTPVerifyResponse(
                    success=False,
                    message=message,
                    payment_id=request.payment_id,
                    verified=False,
                    attempts_remaining=attempts_remaining,
                    locked=False
                )
    
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_otp(
    payment_id: str,
    otp_service: OTPService = Depends(get_otp_service)
):
    try:
        await otp_service.deleteOtpAsync(payment_id)
        return None
    except Exception as e:
        logger.error(f"Error canceling OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel OTP"
        )