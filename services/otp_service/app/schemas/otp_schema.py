from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OTPRequest(BaseModel):
    """Request schema for OTP generation"""
    payment_id: str = Field(..., description="Payment ID")
    tuition_id: str = Field(..., description="Tuition ID")
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., description="Payment amount")
    email: Optional[str] = Field(None, description="User email for OTP delivery")

class OTPVerifyRequest(BaseModel):
    """Request schema for OTP verification"""
    payment_id: str = Field(..., description="Payment ID")
    otp_code: str = Field(..., description="OTP code to verify")

class OTPResendRequest(BaseModel):
    """Request schema for OTP resend"""
    payment_id: str = Field(..., description="Payment ID")

class OTPResponse(BaseModel):
    """Response schema for OTP operations"""
    success: bool
    message: str
    payment_id: str
    expires_in: Optional[int] = Field(None, description="OTP expiration time in seconds")
    attempts_remaining: Optional[int] = Field(None, description="Remaining verification attempts")

class OTPVerifyResponse(BaseModel):
    """Response schema for OTP verification"""
    success: bool
    message: str
    payment_id: str
    verified: bool
    attempts_remaining: Optional[int] = None
    locked: Optional[bool] = False

class OTPData(BaseModel):
    """OTP data stored in Redis"""
    otp_code: str
    payment_id: str
    tuition_id: str
    user_id: str
    amount: float
    attempts: int = 0
    created_at: str
    email: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "otp_code": "123456",
                "payment_id": "pay_123",
                "tuition_id": "tuition_456",
                "user_id": "user_789",
                "amount": 1000.00,
                "attempts": 0,
                "created_at": "2025-11-15T10:30:00",
                "email": "user@example.com"
            }
        }
