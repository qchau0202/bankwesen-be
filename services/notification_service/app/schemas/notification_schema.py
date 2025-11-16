from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

class EmailOTPRequest(BaseModel):
    """Request schema for sending OTP email"""
    email: EmailStr = Field(..., description="Recipient email address")
    otp_code: str = Field(..., description="OTP code to send")
    expires_in: int = Field(..., description="OTP expiration time in seconds")
    payment_id: str = Field(..., description="Payment ID")
    amount: float = Field(..., description="Payment amount")

class EmailTransactionRequest(BaseModel):
    """Request schema for sending transaction confirmation email"""
    recipient_email: EmailStr = Field(..., description="Recipient (student) email address")
    payer_email: EmailStr = Field(..., description="Payer (customer) email address")
    transaction_id: str = Field(..., description="Transaction ID")
    payment_id: str = Field(..., description="Payment ID")
    amount: float = Field(..., description="Transaction amount")
    payer_name: str = Field(..., description="Name of customer who paid")
    recipient_name: str = Field(..., description="Name of student who receives payment")
    is_self_payment: bool = Field(..., description="Whether customer is paying for themselves")
    tuition_info: Optional[Dict[str, Any]] = Field(None, description="Tuition information")
    timestamp: str = Field(..., description="Transaction timestamp")

class EmailResponse(BaseModel):
    """Response schema for email operations"""
    success: bool
    message: str
    email_sent_to: Optional[list[str]] = None
