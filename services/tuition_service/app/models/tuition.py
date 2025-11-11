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


class StudentModel(BaseModel):
    """Student model for tuition_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    studentid: str = Field(..., description="Unique student ID (PK)")
    student_name: str = Field(..., description="Student full name")
    student_code: str = Field(..., description="Student code/number")
    email: EmailStr = Field(..., description="Student email")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "studentid": "ST1731369600",
                "student_name": "John Doe",
                "student_code": "523K0000",
                "email": "john.doe@student.edu"
            }
        }


class TuitionModel(BaseModel):
    """Tuition model for tuition_db."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tuitionid: str = Field(..., description="Unique tuition ID (PK)")
    studentid: str = Field(..., description="Foreign key to Student")
    semester: str = Field(..., description="Semester: 'Semester I', 'Semester II', or 'Summer Semester'")
    year: str = Field(..., description='Academic year range in the format "YYYY-YYYY" (e.g. "2023-2024")')
    tuition_ammount: float = Field(..., description="Tuition amount due")
    due_date: datetime = Field(..., description="Payment due date")
    payment_status: str = Field(default="pending", description="Status: pending, partial, paid")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "tuitionid": "TU1731369600001",
                "studentid": "ST1731369600",
                "semester": "Semester I",
                "year": "2023-2024",
                "tuition_ammount": 5000.00,
                "due_date": "2024-12-31T23:59:59",
                "payment_status": "pending"
            }
        }
