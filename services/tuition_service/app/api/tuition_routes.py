from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, Optional
from app.db.mongodb import get_database
from app.services.tuition_service import TuitionService
from app.schemas.tuition import StudentTuitionListResponse, TuitionResponse, ErrorResponse
from app.core.security import get_current_user, verify_api_key

router = APIRouter(prefix="/api/tuition", tags=["Tuition"])


def get_tuition_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TuitionService:
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
    return await tuition_service.getStudentTuitionsAsync(studentId, None, None)


@router.get(
    "/record/{tuitionId}",
    response_model=TuitionResponse,
    responses={
        200: {
            "description": "Successfully retrieved tuition record",
            "model": TuitionResponse
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token",
            "model": ErrorResponse
        },
        404: {
            "description": "Tuition record not found",
            "model": ErrorResponse
        }
    },
    summary="Get a specific tuition record by tuitionId",
    description="""
    Retrieve a detailed tuition record using its unique tuitionId.

    **Authentication Required:**
    - Valid JWT Bearer token via `Authorization` header
    - API key via `x-api-key` header
    """
)
async def get_tuition_record(
    tuitionId: str,
    tuition_service: TuitionService = Depends(get_tuition_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    api_key: str = Depends(verify_api_key)
) -> TuitionResponse:
    try:
        return await tuition_service.getTuitionByIdAsync(tuitionId)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
