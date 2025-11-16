from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, TYPE_CHECKING
import logging

from app.schemas.payment_schema import (
    PaymentCreateRequest,
    PaymentResponse,
    OTPRequestResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    PaymentCancelResponse,
    ErrorResponse
)
from app.services.payment_service import PaymentService
from app.db.mongodb import get_database
from app.core.security import verify_api_key, get_current_user, security

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["Payment"], dependencies=[Depends(verify_api_key)])


async def get_payment_service(db: Any = Depends(get_database)) -> PaymentService:
    """Dependency to get payment service"""
    return PaymentService(db)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Payment created successfully"},
        409: {"model": ErrorResponse, "description": "Payment already exists"},
        404: {"model": ErrorResponse, "description": "Tuition not found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    }
)
async def create_payment(
    request: PaymentCreateRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new payment for all debt tuitions of a student.
    
    Only requires studentId - automatically fetches and pays ALL unpaid tuitions for that student.
    Customer ID and email are automatically extracted from the JWT token (who is paying).
    
    Flow: OTP Page -> Message Broker (notify other services) -> Lock service
    
    - Automatically fetches all debt tuitions for the specified student
    - Locks the payment to allow only one payment per tuition per customer
    - Uses idempotency key to prevent duplicate payments
    - Notifies other services via message broker
    """
    try:
        # Extract customer ID and email from JWT token
        customer_id = current_user.get("customerId")
        user_email = current_user.get("email")
        
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID not found in authentication token"
            )
        
        logger.info(f"Creating payment for customer {customer_id}, student {request.studentId} (all debt tuitions)")
        
        # Extract JWT token for internal service calls
        auth_token = credentials.credentials
        
        payment = await payment_service.createPaymentAsync(request, auth_token, customer_id, user_email)
        
        return PaymentResponse(
            paymentId=payment.paymentId,
            customerId=payment.customerId,
            tuitionIds=payment.tuitionIds,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            status=payment.status,
            otp_attempts=payment.otp_attempts,
            is_locked=payment.is_locked,
            created_at=payment.created_at,
            expired_at=payment.expired_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{paymentID}/otp",
    response_model=OTPRequestResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP sent successfully"},
        404: {"model": ErrorResponse, "description": "Payment not found"},
        423: {"model": ErrorResponse, "description": "Payment locked"},
        400: {"model": ErrorResponse, "description": "Invalid payment status"},
    }
)
async def request_payment_otp(
    paymentID: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Request OTP for payment verification.
    
    Flow: Immediately send OTP (expiration: 60s) -> User inputs OTP code
    
    - OTP expires in 60 seconds
    - Can be resent if expired
    - Calls internal OTP service API
    - Email is automatically extracted from JWT token
    """
    try:
        logger.info(f"Requesting OTP for payment {paymentID}")
        
        # Get email from JWT token
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found in authentication token"
            )
        
        otp_response = await payment_service.requestOtpAsync(paymentID, user_email)
        
        return OTPRequestResponse(
            success=otp_response.get("success", True),
            message=otp_response.get("message", "OTP sent successfully"),
            payment_id=otp_response.get("payment_id", paymentID),
            expires_in=otp_response.get("expires_in", 60),
            attempts_remaining=otp_response.get("attempts_remaining", 3)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{paymentID}/verify-otp",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP verified and payment completed"},
        400: {"model": ErrorResponse, "description": "Invalid OTP or max attempts"},
        404: {"model": ErrorResponse, "description": "Payment not found"},
        423: {"model": ErrorResponse, "description": "Payment locked after max attempts"},
    }
)
async def verify_payment_otp(
    paymentID: str,
    request: OTPVerifyRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify OTP and complete payment.
    
    Flow: System verifies OTP code
    
    SUCCESS:
    - OTP verified -> Update tuition balance -> Complete payment
    
    FAILED:
    - EXPIRED: Resend button becomes active (use POST /{paymentID}/otp)
    - WRONG OTP: User can retry up to 3 times
    - MAX ATTEMPTS: Payment cancelled automatically, user must create new payment
    """
    try:
        logger.info(f"Verifying OTP for payment {paymentID}")
        
        # Extract JWT token for internal service calls
        auth_token = credentials.credentials
        
        payment = await payment_service.verifyOtpAsync(paymentID, request.otp_code, auth_token)
        
        return OTPVerifyResponse(
            success=True,
            message="Payment completed successfully",
            payment=PaymentResponse(
                paymentId=payment.paymentId,
                customerId=payment.customerId,
                tuitionIds=payment.tuitionIds,
                idempotency_key=payment.idempotency_key,
                amount=payment.amount,
                status=payment.status,
                otp_attempts=payment.otp_attempts,
                is_locked=payment.is_locked,
                created_at=payment.created_at,
                expired_at=payment.expired_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{paymentID}/cancel",
    response_model=PaymentCancelResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Payment cancelled successfully"},
        404: {"model": ErrorResponse, "description": "Payment not found"},
        400: {"model": ErrorResponse, "description": "Cannot cancel payment"},
    }
)
async def cancel_payment(
    paymentID: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancel a payment.
    
    Flow: Multiple wrong OTP or user cancel -> Payment cancelled
    
    - User can cancel payment manually
    - Payment auto-cancelled after 3 failed OTP attempts
    - Can only cancel payments with 'pending' status
    """
    try:
        logger.info(f"Cancelling payment {paymentID}")
        
        await payment_service.cancelPaymentAsync(paymentID)
        
        return PaymentCancelResponse(
            success=True,
            message="Payment cancelled successfully",
            payment_id=paymentID
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{paymentID}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Payment retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Payment not found"},
    }
)
async def get_payment(
    paymentID: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get payment details by payment ID.
    
    - Returns payment information
    - Can be used to check payment status and history
    """
    try:
        logger.info(f"Getting payment {paymentID}")
        
        payment = await payment_service.get_payment(paymentID)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return PaymentResponse(
            paymentId=payment.paymentId,
            customerId=payment.customerId,
            tuitionIds=payment.tuitionIds,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            status=payment.status,
            otp_attempts=payment.otp_attempts,
            is_locked=payment.is_locked,
            created_at=payment.created_at,
            expired_at=payment.expired_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
