from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, Optional
from app.db.mongodb import get_database
from app.services.tuition_service import TuitionService
from app.schemas.tuition import StudentTuitionListResponse, TuitionResponse, ErrorResponse
from app.core.security import get_current_user, verify_api_key

router = APIRouter(prefix="/api/tuition", tags=["Tuition"])


def get_tuition_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TuitionService:
    """Dependency to get tuition service instance."""
    return TuitionService(db)


@router.get(
    "/{studentId}",
    response_model=StudentTuitionListResponse,
    responses={
        200: {
            "description": "Successfully retrieved student tuition information",
            "model": StudentTuitionListResponse
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token",
            "model": ErrorResponse
        },
        403: {
            "description": "Forbidden - User can only access their own tuition records",
            "model": ErrorResponse
        },
        404: {
            "description": "Student not found or no tuition records exist",
            "model": ErrorResponse
        }
    },
    summary="Get tuition info for a student (Authentication Required)",
    description="""
    Retrieve all tuition records for a specific student by their student ID.
    
    **Authentication Required:** 
    - Must provide a valid JWT Bearer token in `Authorization` header
    - Must provide API key in `x-api-key` header
    
    **Access Control:** 
    - Any authenticated student can view any student's tuition records
    - This allows students to help pay for each other's tuition fees
    - Students can view their own records or other students' records for payment purposes
    
    Returns:
    - Student information (ID, name, email)
    - List of all tuition records with details
    - Total number of tuition records
    - Total outstanding debt in VND
    - Formatted debt amount string
    
    All currency values are in Vietnamese Dong (VND).
    """
)
async def get_student_tuition(
    studentId: str,
    tuition_service: TuitionService = Depends(get_tuition_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    api_key: str = Depends(verify_api_key)
) -> StudentTuitionListResponse:
    """
    Get tuition information for a specific student.
    
    Args:
        studentId: The student's ID/code (e.g., "523K0001")
        current_user: Current authenticated user from JWT token
        api_key: API key for service authentication
        
    Returns:
        StudentTuitionListResponse containing all tuition records and summary
        
    Note:
        Any authenticated student can view any student's tuition records.
        This design allows students to help pay for each other's tuition fees,
        supporting scenarios where friends or family assist with payments.
    """
    # Allow any authenticated student to view tuition records
    # This enables students to help pay for each other's tuition
    
    return await tuition_service.getStudentTuitionsAsync(studentId, None, None)
