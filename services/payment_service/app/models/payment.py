from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, _handler=None):
        field_schema.update(type="string")


class PaymentModel(BaseModel):
    """Payment model for payment_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    paymentId: str = Field(..., description="Unique payment ID (PK)")
    customerId: str = Field(..., description="Foreign key to Customer (from auth_db)")
    tuitionId: str = Field(..., description="Foreign key to Tuition")
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate payments")
    amount: float = Field(..., description="Payment amount")
    status: str = Field(default="pending", description="Status: pending, completed, failed, cancelled")
    otp_attempts: int = Field(default=0, description="Number of OTP verification attempts")
    is_locked: bool = Field(default=False, description="Whether payment is locked due to multiple failures")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expired_at: Optional[datetime] = Field(None, description="Payment expiration date")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "paymentId": "PAY1731369600001",
                "customerId": "523K0000",
                "tuitionId": "TU1731369600001",
                "idempotency_key": "unique-key-12345",
                "amount": 5000000.00,
                "status": "completed",
                "otp_attempts": 1,
                "is_locked": False,
                "expired_at": "2024-12-31T23:59:59"
            }
        }
