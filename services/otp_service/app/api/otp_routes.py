from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.otp_schema import (
    OTPRequest,
    OTPVerifyRequest,
    OTPResendRequest,
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
    """Dependency to get OTP service"""
    return OTPService(redis_client)

@router.post("/request", response_model=OTPResponse, status_code=status.HTTP_201_CREATED)
async def request_otp(
    request: OTPRequest,
    otp_service: OTPService = Depends(get_otp_service)
):
    """
    Generate and send OTP for payment
    
    Flow: User requests OTP -> System generates OTP -> Sends email (if email provided)
    """
    try:
        # Check if payment is locked
        is_locked = await otp_service.is_payment_locked(request.payment_id)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to too many failed attempts. Please try again later."
            )
        
        # Generate OTP
        otp_code, otp_data = await otp_service.generate_otp(request)
        
        # Get expiration time
        expires_in = await otp_service.get_remaining_time(request.payment_id)
        attempts_remaining = await otp_service.get_attempts_remaining(request.payment_id)
        
        # Send OTP via email using notification service
        if request.email:
            try:
                async with httpx.AsyncClient() as client:
                    notification_response = await client.post(
                        f"{settings.NOTIFICATION_SERVICE_URL}/api/notification/email-otp",
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
                        # Continue anyway, log OTP for testing
                        logger.info(f"OTP for payment {request.payment_id}: {otp_code}")
                    else:
                        logger.info(f"OTP email sent successfully to {request.email}")
            except Exception as e:
                logger.error(f"Error sending OTP email: {e}")
                # Log OTP for testing purposes
                logger.info(f"OTP for payment {request.payment_id}: {otp_code}")
        else:
            # No email provided, log OTP
            logger.info(f"OTP for payment {request.payment_id}: {otp_code}")
        
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
    """
    Verify OTP code
    
    Flow: User submits OTP -> System verifies OTP -> Returns verification result
    
    Success: OTP is valid, payment can proceed
    Failure: 
        - Invalid OTP: User can retry (max 3 attempts)
        - Expired OTP: User needs to request resend
        - Locked: Too many failed attempts, payment is canceled
    """
    try:
        is_valid, message, attempts_remaining = await otp_service.verify_otp(
            request.payment_id,
            request.otp_code
        )
        
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
            is_locked = await otp_service.is_payment_locked(request.payment_id)
            
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

@router.post("/resend", response_model=OTPResponse)
async def resend_otp(
    request: OTPResendRequest,
    otp_service: OTPService = Depends(get_otp_service)
):
    """
    Resend OTP (when expired)
    
    Flow: User clicks resend -> System generates new OTP -> Sends email
    """
    try:
        # Check if payment is locked
        is_locked = await otp_service.is_payment_locked(request.payment_id)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to too many failed attempts. Please try again later."
            )
        
        # Resend OTP
        otp_code, otp_data = await otp_service.resend_otp(request.payment_id)
        
        if not otp_code or not otp_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No OTP data found for this payment. Please request a new OTP."
            )
        
        # Get expiration time
        expires_in = await otp_service.get_remaining_time(request.payment_id)
        attempts_remaining = await otp_service.get_attempts_remaining(request.payment_id)
        
        # Send OTP via email using notification service
        if otp_data.email:
            try:
                async with httpx.AsyncClient() as client:
                    notification_response = await client.post(
                        f"{settings.NOTIFICATION_SERVICE_URL}/api/notification/email-otp",
                        json={
                            "email": otp_data.email,
                            "otp_code": otp_code,
                            "expires_in": expires_in,
                            "payment_id": request.payment_id,
                            "amount": otp_data.amount
                        },
                        headers={settings.API_KEY_NAME: settings.API_KEY},
                        timeout=10.0
                    )
                    
                    if notification_response.status_code != 200:
                        logger.warning(f"Failed to resend OTP email: {notification_response.text}")
                        logger.info(f"Resent OTP for payment {request.payment_id}: {otp_code}")
                    else:
                        logger.info(f"OTP email resent successfully to {otp_data.email}")
            except Exception as e:
                logger.error(f"Error resending OTP email: {e}")
                logger.info(f"Resent OTP for payment {request.payment_id}: {otp_code}")
        else:
            logger.info(f"Resent OTP for payment {request.payment_id}: {otp_code}")
        
        return OTPResponse(
            success=True,
            message="OTP resent successfully. Check your email.",
            payment_id=request.payment_id,
            expires_in=expires_in,
            attempts_remaining=attempts_remaining
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
        )

@router.get("/{payment_id}/status", response_model=OTPResponse)
async def get_otp_status(
    payment_id: str,
    otp_service: OTPService = Depends(get_otp_service)
):
    """
    Get OTP status for a payment
    
    Returns: OTP expiration time and remaining attempts
    """
    try:
        # Check if OTP exists
        otp_data = await otp_service.get_otp_data(payment_id)
        
        if not otp_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active OTP found for this payment"
            )
        
        # Check if locked
        is_locked = await otp_service.is_payment_locked(payment_id)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to too many failed attempts"
            )
        
        # Get remaining time and attempts
        expires_in = await otp_service.get_remaining_time(payment_id)
        attempts_remaining = await otp_service.get_attempts_remaining(payment_id)
        
        return OTPResponse(
            success=True,
            message="OTP is active",
            payment_id=payment_id,
            expires_in=expires_in,
            attempts_remaining=attempts_remaining
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OTP status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OTP status"
        )

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_otp(
    payment_id: str,
    otp_service: OTPService = Depends(get_otp_service)
):
    """
    Cancel OTP and delete all related data
    
    Used when payment is canceled or user chooses to cancel
    """
    try:
        await otp_service.delete_otp(payment_id)
        return None
    except Exception as e:
        logger.error(f"Error canceling OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel OTP"
        )
