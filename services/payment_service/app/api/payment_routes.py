from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, TYPE_CHECKING, List
import logging

from app.schemas.payment_schema import (
    PaymentCreateRequest,
    PaymentResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    PaymentCancelResponse,
    PaymentHistoryResponse,
    PaymentRecordResponse,
    TuitionDetailResponse,
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
            created_at=payment.created_at,
            otp_expires_in=getattr(payment, 'otp_expires_in', None)
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
    try:
        logger.info(f"Verifying OTP for payment {paymentID}")
        
        # Extract JWT token for internal service calls
        auth_token = credentials.credentials
        
        result = await payment_service.verifyOtpAsync(paymentID, request.otp_code, auth_token)
        payment = result["payment"]
        
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
                created_at=payment.created_at
            ),
            new_access_token=result.get("new_access_token"),
            token_type=result.get("token_type"),
            expires_in=result.get("expires_in")
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
    "/record",
    response_model=PaymentHistoryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Payment history retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Failed to fetch payment records"}
    }
)
async def get_payment_records(
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    customer_id = current_user.get("customerId")
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID not found in authentication token"
        )

    auth_token = credentials.credentials
    raw_records = await payment_service.getCustomerPaymentRecordsAsync(customer_id, auth_token)

    formatted_records: List[PaymentRecordResponse] = []
    for record in raw_records:
        payment = record["payment"]
        tuitions = record.get("tuitions", [])

        payment_response = PaymentResponse(
            paymentId=payment.paymentId,
            customerId=payment.customerId,
            tuitionIds=payment.tuitionIds,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            status=payment.status,
            created_at=payment.created_at,
            otp_expires_in=None
        )

        tuition_responses = []
        for tuition in tuitions:
            try:
                tuition_responses.append(TuitionDetailResponse(**tuition))
            except Exception as e:
                logger.warning(f"Skipping tuition detail due to validation error: {e}")

        formatted_records.append(
            PaymentRecordResponse(
                payment=payment_response,
                tuitions=tuition_responses
            )
        )

    return PaymentHistoryResponse(
        customerId=customer_id,
        total_payments=len(formatted_records),
        payments=formatted_records
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
    try:
        logger.info(f"Getting payment {paymentID}")
        
        payment = await payment_service.getPaymentAsync(paymentID)
        
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
            created_at=payment.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
