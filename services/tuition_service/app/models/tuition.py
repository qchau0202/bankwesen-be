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


class TuitionModel(BaseModel):
    """Tuition model for tuition_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tuitionId: str = Field(..., description="Unique tuition ID (PK)")
    studentId: str = Field(..., description="Student ID/code")
    semester: str = Field(..., description="Semester: 'Semester I', 'Semester II', or 'Summer Semester'")
    academic_year: str = Field(..., description='Academic year range in the format "YYYY-YYYY" (e.g. "2023-2024")')
    tuition_debt: float = Field(..., description="Tuition debt amount")
    due_date: datetime = Field(..., description="Payment due date")
    status: str = Field(default="pending", description="Status: pending, partial, paid")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "tuitionId": "TU1731369600001",
                "studentId": "523K0001",
                "semester": "Semester I",
                "academic_year": "2023-2024",
                "tuition_debt": 5000.00,
                "due_date": "2024-12-31T23:59:59",
                "status": "pending"
            }
        }
