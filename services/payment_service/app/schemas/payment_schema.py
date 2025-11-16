from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Union
from datetime import datetime


# Request Schemas
class PaymentCreateRequest(BaseModel):
    """Request schema for creating a new payment. Customer ID is extracted from JWT token."""
    tuitionIds: Union[str, List[str]] = Field(
        ..., 
        description="Single tuition ID or list of tuition IDs to be paid. Use 'all' to pay all unpaid tuitions for the student."
    )
    studentId: Optional[str] = Field(
        None,
        description="Student ID whose tuitions to pay. Required when tuitionIds='all'. If not provided, uses the authenticated user's ID from JWT token."
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "tuitionIds": "TU1731369600001"
                },
                {
                    "tuitionIds": ["TU1731369600001", "TU1731369600002"]
                },
                {
                    "tuitionIds": "all",
                    "studentId": "523K0001"
                },
                {
                    "tuitionIds": "all"
                }
            ]
        }


class OTPVerifyRequest(BaseModel):
    """Request schema for OTP verification"""
    otp_code: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "otp_code": "123456"
            }
        }


# Response Schemas
class PaymentResponse(BaseModel):
    """Response schema for payment information"""
    paymentId: str
    customerId: str
    tuitionIds: List[str]
    idempotency_key: str
    amount: float
    status: str
    otp_attempts: int
    is_locked: bool
    created_at: datetime
    expired_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "paymentId": "PAY1731369600001",
                "customerId": "523K0000",
                "tuitionIds": ["TU1731369600001", "TU1731369600002"],
                "idempotency_key": "unique-key-12345",
                "amount": 10000000.00,
                "status": "pending",
                "otp_attempts": 0,
                "is_locked": False,
                "created_at": "2024-11-15T10:00:00",
                "expired_at": "2024-11-15T11:00:00"
            }
        }


class OTPRequestResponse(BaseModel):
    """Response schema for OTP request"""
    success: bool
    message: str
    payment_id: str
    expires_in: int
    attempts_remaining: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "OTP sent successfully to your email",
                "payment_id": "PAY1731369600001",
                "expires_in": 60,
                "attempts_remaining": 3
            }
        }


class OTPVerifyResponse(BaseModel):
    """Response schema for OTP verification"""
    success: bool
    message: str
    payment: Optional[PaymentResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Payment completed successfully",
                "payment": {
                    "paymentId": "PAY1731369600001",
                    "customerId": "523K0000",
                    "tuitionIds": ["TU1731369600001"],
                    "idempotency_key": "unique-key-12345",
                    "amount": 5000000.00,
                    "status": "completed",
                    "otp_attempts": 1,
                    "is_locked": False,
                    "created_at": "2024-11-15T10:00:00",
                    "expired_at": None
                }
            }
        }


class PaymentCancelResponse(BaseModel):
    """Response schema for payment cancellation"""
    success: bool
    message: str
    payment_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Payment cancelled successfully",
                "payment_id": "PAY1731369600001"
            }
        }


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Payment not found"
            }
        }
