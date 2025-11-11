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


class TransactionModel(BaseModel):
    """Transaction model for transaction_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    transactionid: str = Field(..., description="Unique transaction ID (PK)")
    paymentid: str = Field(..., description="Foreign key to Payment")
    tuitionid: str = Field(..., description="Foreign key to Tuition")
    userid: str = Field(..., description="Foreign key to User")
    ammount: float = Field(..., description="Transaction amount")
    status: str = Field(default="pending", description="Status: pending, completed, failed, refunded")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transaction timestamp")
    method: str = Field(default="online", description="Payment method: online, cash, bank_transfer, credit_card")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "transactionid": "TXN1731369600001",
                "paymentid": "PAY1731369600001",
                "tuitionid": "TU1731369600001",
                "userid": "ST1731369600",
                "ammount": 5000.00,
                "status": "completed",
                "timestamp": "2024-11-11T10:30:00",
                "method": "online"
            }
        }
