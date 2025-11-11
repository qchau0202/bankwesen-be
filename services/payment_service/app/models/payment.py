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
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class PaymentModel(BaseModel):
    """Payment model for payment_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    paymentid: str = Field(..., description="Unique payment ID (PK)")
    studentid: str = Field(..., description="Foreign key to Student (from tuition_db)")
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate payments")
    userid: str = Field(..., description="Foreign key to User (from auth_db)")
    tuitionid: str = Field(..., description="Foreign key to Tuition")
    ammount: float = Field(..., description="Payment amount")
    status: str = Field(default="pending", description="Status: pending, completed, failed")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "paymentid": "PAY1731369600001",
                "studentid": "ST1731369600",
                "idempotency_key": "unique-key-12345",
                "userid": "ST1731369600",
                "tuitionid": "TU1731369600001",
                "ammount": 5000.00,
                "status": "completed"
            }
        }
