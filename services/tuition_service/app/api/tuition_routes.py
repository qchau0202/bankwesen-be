from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any
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
    
    return await tuition_service.getStudentTuitionsAsync(studentId)


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
        403: {
            "description": "Forbidden - User can only access their own tuition records",
            "model": ErrorResponse
        },
        404: {
            "description": "Tuition record not found",
            "model": ErrorResponse
        }
    },
    summary="Get specific tuition record (Authentication Required)",
    description="""
    Retrieve a specific tuition record by its tuition ID. 
    
    **Authentication Required:** 
    - Must provide a valid JWT Bearer token in `Authorization` header
    - Must provide API key in `x-api-key` header
    
    **Access Control:** 
    - Any authenticated student can view any tuition record
    - This allows students to help pay for each other's tuition fees
    
    Currency is in Vietnamese Dong (VND).
    """
)
async def get_tuition_record(
    tuitionId: str,
    tuition_service: TuitionService = Depends(get_tuition_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    api_key: str = Depends(verify_api_key)
) -> TuitionResponse:
    """
    Get a specific tuition record by tuition ID.
    
    Args:
        tuitionId: The tuition record ID (e.g., "TU2024110001")
        current_user: Current authenticated user from JWT token
        api_key: API key for service authentication
        
    Returns:
        TuitionResponse containing the tuition record details
        
    Note:
        Any authenticated student can view any tuition record.
        This design allows students to help pay for each other's tuition fees.
    """
    # Allow any authenticated student to view tuition records
    # This enables students to help pay for each other's tuition
    tuition_record = await tuition_service.getTuitionByIdAsync(tuitionId)
    
    return tuition_record


@router.put(
    "/{tuitionId}/status",
    response_model=TuitionResponse,
    responses={
        200: {
            "description": "Successfully updated tuition status",
            "model": TuitionResponse
        },
        400: {
            "description": "Invalid status value",
            "model": ErrorResponse
        },
        404: {
            "description": "Tuition record not found",
            "model": ErrorResponse
        }
    },
    summary="Update tuition status (Internal Service Only)",
    description="""
    Update the status of a tuition record.
    This endpoint is intended for internal service use.
    
    **API Key Required:**
    - Must provide API key in `x-api-key` header
    
    Valid statuses:
    - "debt": Student has outstanding tuition
    - "paid": Tuition has been paid
    """
)
async def update_tuition_status(
    tuitionId: str,
    status_update: Dict[str, Any],
    tuition_service: TuitionService = Depends(get_tuition_service),
    api_key: str = Depends(verify_api_key)
) -> TuitionResponse:
    """
    Update tuition status.
    
    Args:
        tuitionId: The tuition record ID (e.g., "TU2024110001")
        status_update: Dictionary containing "status" key with value "debt" or "paid"
        api_key: API key for service authentication
        
    Returns:
        Updated TuitionResponse
    """
    status = status_update.get("status")
    if not status:
        raise HTTPException(
            status_code=400,
            detail="Missing 'status' field in request body"
        )
    
    return await tuition_service.updateTuitionStatusAsync(tuitionId, status)


@router.get(
    "/",
    summary="Tuition Service Info",
    description="Basic information about the Tuition Service API"
)
async def tuition_info():
    """Get information about the tuition service."""
    return {
        "service": "Tuition Service",
        "version": "1.0.0",
        "description": "Manage student tuition records and payments",
        "currency": "VND (Vietnamese Dong)",
        "endpoints": {
            "GET /api/tuition/{studentId}": "Get all tuition records for a student",
            "GET /api/tuition/record/{tuitionId}": "Get specific tuition record by ID",
            "PUT /api/tuition/{tuitionId}/status": "Update tuition status (Internal)"
        }
    }
