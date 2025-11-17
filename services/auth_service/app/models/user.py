from typing import Optional
from pydantic import BaseModel, Field, EmailStr
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


class UserModel(BaseModel):
    """User model matching the MongoDB schema."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    customerId: str = Field(..., description="Unique customer ID")
    username: str = Field(..., description="Username for login")
    password_hash: str = Field(..., description="Hashed password (bcrypt)")
    full_name: Optional[str] = Field(None, description="Full name of the user")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone_number: Optional[str] = Field(None, description="Phone number")
    balance: float = Field(default=0.0, description="Account balance")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "customerId": "523K0000",
                "username": "student1",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OMxZJ.hY8h6.",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "balance": 1000.0
            }
        }


class UserInDB(BaseModel):
    """User model with hashed password for database operations."""
    customerId: str
    username: str
    password_hash: str
    role: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    balance: float = 0.0
