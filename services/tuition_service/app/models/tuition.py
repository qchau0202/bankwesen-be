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
    """Tuition model for tuition_db with student information."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tuitionId: str = Field(..., description="Unique tuition ID (PK)")
    
    # Student Information
    studentId: str = Field(..., description="Student ID/code")
    studentName: str = Field(..., description="Full name of the student")
    studentEmail: EmailStr = Field(..., description="Student email address")
    
    # Tuition Information
    semester: str = Field(..., description="Semester: 'Semester I', 'Semester II', or 'Summer Semester'")
    academic_year: str = Field(..., description='Academic year range in the format "YYYY-YYYY" (e.g. "2023-2024")')
    tuition_amount: float = Field(..., description="Tuition amount in Vietnamese Dong (VND)")
    status: str = Field(default="debt", description="Status: debt, paid")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "tuitionId": "TU1731369600001",
                "studentId": "523K0001",
                "studentName": "Nguyen Van A",
                "studentEmail": "nguyenvana@student.edu.vn",
                "semester": "Semester I",
                "academic_year": "2024-2025",
                "tuition_amount": 15000000.00,
                "status": "debt",
                "created_at": "2024-11-15T10:00:00"
            }
        }
