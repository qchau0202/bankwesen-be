from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# Request Schemas
class PaymentCreateRequest(BaseModel):
    """Request schema for creating a new payment. Customer ID is extracted from JWT token. Only requires studentId - automatically pays all debt tuitions."""
    studentId: str = Field(
        ...,
        description="Student ID whose debt tuitions to pay. The system will automatically fetch and pay all unpaid tuitions for this student."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "studentId": "523K0001"
            }
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
    created_at: datetime
    otp_expires_in: Optional[int] = Field(None, description="OTP expiration time in seconds (60 seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "paymentId": "PAY1731369600001",
                "customerId": "523K0000",
                "tuitionIds": ["TU1731369600001", "TU1731369600002"],
                "idempotency_key": "unique-key-12345",
                "amount": 10000000.00,
                "status": "pending",
                "created_at": "2024-11-15T10:00:00",
                "otp_expires_in": 60
            }
        }

class TuitionDetailResponse(BaseModel):
    """Response schema for individual tuition detail pulled from tuition service"""
    tuitionId: str
    studentId: str
    studentName: str
    studentEmail: EmailStr
    semester: str
    academic_year: str
    tuition_amount: float
    status: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "tuitionId": "TU1731369600001",
                "studentId": "523K0001",
                "studentName": "Nguyen Van A",
                "studentEmail": "nguyenvana@student.edu.vn",
                "semester": "Semester I",
                "academic_year": "2024-2025",
                "tuition_amount": 15000000.0,
                "status": "paid",
                "created_at": "2024-11-15T10:00:00"
            }
        }

class PaymentRecordResponse(BaseModel):
    """Combined payment + tuition detail response"""
    payment: PaymentResponse
    tuitions: List[TuitionDetailResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "payment": PaymentResponse.Config.json_schema_extra["example"],
                "tuitions": [TuitionDetailResponse.Config.json_schema_extra["example"]]
            }
        }

class PaymentHistoryResponse(BaseModel):
    """Wrapper response for all payment records made by a customer"""
    customerId: str
    total_payments: int
    payments: List[PaymentRecordResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "customerId": "523K0000",
                "total_payments": 1,
                "payments": [PaymentRecordResponse.Config.json_schema_extra["example"]]
            }
        }


class OTPVerifyResponse(BaseModel):
    """Response schema for OTP verification"""
    success: bool
    message: str
    payment: Optional[PaymentResponse] = None
    new_access_token: Optional[str] = Field(None, description="New JWT access token with updated balance")
    token_type: Optional[str] = Field(None, description="Token type (bearer)")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
    
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
                    "created_at": "2024-11-15T10:00:00"
                },
                "new_access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
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
