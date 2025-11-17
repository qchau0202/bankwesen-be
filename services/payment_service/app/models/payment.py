from typing import Optional, List
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
    tuitionIds: List[str] = Field(..., description="List of tuition IDs to be paid")
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate payments")
    amount: float = Field(..., description="Total payment amount")
    status: str = Field(default="pending", description="Status: pending, completed, failed, cancelled")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "paymentId": "PAY1731369600001",
                "customerId": "523K0000",
                "tuitionIds": ["TU1731369600001", "TU1731369600002"],
                "idempotency_key": "unique-key-12345",
                "amount": 10000000.00,
                "status": "completed"
            }
        }
