from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class TuitionResponse(BaseModel):
    tuitionId: str
    studentId: str
    studentName: str
    studentEmail: EmailStr
    semester: str
    academic_year: str
    tuition_amount: float
    status: str
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "tuitionId": "TU1731369600001",
                "studentId": "523K0001",
                "studentName": "Nguyen Van A",
                "studentEmail": "nguyenvana@student.edu.vn",
                "semester": "Semester I",
                "academic_year": "2024-2025",
                "tuition_amount": 15000000.00,
                "status": "paid",
                "created_at": "2024-11-15T10:00:00"
            }
        }


class StudentTuitionListResponse(BaseModel):
    studentId: str
    studentName: str
    studentEmail: EmailStr
    tuitions: List[TuitionResponse]
    total_tuitions: int
    total_debt: float
    total_debt_vnd: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "studentId": "523K0001",
                "studentName": "Nguyen Van A",
                "studentEmail": "nguyenvana@student.edu.vn",
                "tuitions": [],
                "total_tuitions": 2,
                "total_debt": 30000000.00,
                "total_debt_vnd": "30,000,000 VND"
            }
        }


class ErrorResponse(BaseModel):
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Student not found"
            }
        }
