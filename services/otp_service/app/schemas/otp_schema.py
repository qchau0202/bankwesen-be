from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class OTPRequest(BaseModel):
    payment_id: str = Field(..., description="Payment ID")
    tuition_ids: List[str] = Field(..., description="List of Tuition IDs")
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., description="Payment amount")
    email: Optional[str] = Field(None, description="User email for OTP delivery")
    attempts: int = Field(0, description="Number of attempts")
class OTPVerifyRequest(BaseModel):
    payment_id: str = Field(..., description="Payment ID")
    otp_code: str = Field(..., description="OTP code to verify")

class OTPResponse(BaseModel):
    success: bool
    message: str
    payment_id: str
    expires_in: Optional[int] = Field(None, description="OTP expiration time in seconds")
    attempts_remaining: Optional[int] = Field(None, description="Remaining verification attempts")

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    payment_id: str
    verified: bool
    attempts_remaining: Optional[int] = None
    locked: Optional[bool] = False

class OTPData(BaseModel):
    otp_code: str
    payment_id: str
    tuition_ids: List[str]
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
                "tuition_ids": ["tuition_456", "tuition_457"],
                "user_id": "user_789",
                "amount": 1000.00,
                "attempts": 0,
                "created_at": "2025-11-15T10:30:00",
                "email": "user@example.com"
            }
        }
