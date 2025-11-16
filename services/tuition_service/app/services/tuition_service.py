from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.tuition import TuitionModel
from app.schemas.tuition import TuitionResponse, StudentTuitionListResponse
from fastapi import HTTPException
from datetime import datetime


class TuitionService:
    """Service class for tuition-related operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.tuitions
    
    def _formatCurrency(self, amount: float) -> str:
        """Format amount to VND currency string."""
        return f"{amount:,.0f} VND"
    
    async def getStudentTuitionsAsync(self, student_id: str) -> StudentTuitionListResponse:
        """
        Fetch all tuition records for a specific student.
        
        Args:
            student_id: The student's ID/code
            
        Returns:
            StudentTuitionListResponse with all tuition records
            
        Raises:
            HTTPException: If student not found or no tuition records exist
        """
        # Fetch all tuition records for the student
        cursor = self.collection.find({"studentId": student_id})
        tuitions_data = await cursor.to_list(length=None)
        
        if not tuitions_data:
            raise HTTPException(
                status_code=404,
                detail=f"No tuition records found for student ID: {student_id}"
            )
        
        # Convert MongoDB documents to TuitionResponse objects
        tuitions = []
        student_name = ""
        student_email = ""
        total_debt = 0.0
        
        for tuition_doc in tuitions_data:
            # Store student info from first record
            if not student_name:
                student_name = tuition_doc.get("studentName", "")
                student_email = tuition_doc.get("studentEmail", "")
            
            tuition_response = TuitionResponse(
                tuitionId=tuition_doc.get("tuitionId"),
                studentId=tuition_doc.get("studentId"),
                studentName=tuition_doc.get("studentName"),
                studentEmail=tuition_doc.get("studentEmail"),
                semester=tuition_doc.get("semester"),
                academic_year=tuition_doc.get("academic_year"),
                tuition_amount=tuition_doc.get("tuition_amount"),
                due_date=tuition_doc.get("due_date"),
                status=tuition_doc.get("status", "debt"),
                created_at=tuition_doc.get("created_at", datetime.utcnow()),
                updated_at=tuition_doc.get("updated_at")
            )
            tuitions.append(tuition_response)
            
            # Calculate total debt (only pending and partial payments)
            if tuition_doc.get("status") in ["debt"]:
                total_debt += tuition_doc.get("tuition_amount", 0.0)
        
        # Sort tuitions by academic year and semester
        tuitions.sort(key=lambda x: (x.academic_year, x.semester), reverse=True)
        
        return StudentTuitionListResponse(
            studentId=student_id,
            studentName=student_name,
            studentEmail=student_email,
            tuitions=tuitions,
            total_tuitions=len(tuitions),
            total_debt=total_debt,
            total_debt_vnd=self._formatCurrency(total_debt)
        )
    
    async def getTuitionByIdAsync(self, tuition_id: str) -> TuitionResponse:
        """
        Fetch a specific tuition record by tuition ID.
        
        Args:
            tuition_id: The tuition record ID
            
        Returns:
            TuitionResponse object
            
        Raises:
            HTTPException: If tuition record not found
        """
        tuition_doc = await self.collection.find_one({"tuitionId": tuition_id})
        
        if not tuition_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Tuition record not found: {tuition_id}"
            )
        
        return TuitionResponse(
            tuitionId=tuition_doc.get("tuitionId"),
            studentId=tuition_doc.get("studentId"),
            studentName=tuition_doc.get("studentName"),
            studentEmail=tuition_doc.get("studentEmail"),
            semester=tuition_doc.get("semester"),
            academic_year=tuition_doc.get("academic_year"),
            tuition_amount=tuition_doc.get("tuition_amount"),
            due_date=tuition_doc.get("due_date"),
            status=tuition_doc.get("status", "debt"),
            created_at=tuition_doc.get("created_at", datetime.utcnow()),
            updated_at=tuition_doc.get("updated_at")
        )
    
    async def updateTuitionStatusAsync(self, tuition_id: str, status: str) -> TuitionResponse:
        """
        Update the status of a tuition record.
        
        Args:
            tuition_id: The tuition record ID
            status: New status ("debt" or "paid")
            
        Returns:
            Updated TuitionResponse object
            
        Raises:
            HTTPException: If tuition record not found or invalid status
        """
        # Validate status
        valid_statuses = ["debt", "paid"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if tuition exists
        tuition_doc = await self.collection.find_one({"tuitionId": tuition_id})
        if not tuition_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Tuition record not found: {tuition_id}"
            )
        
        # Update the tuition record
        result = await self.collection.update_one(
            {"tuitionId": tuition_id},
            {"$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to update tuition status"
            )
        
        # Return updated tuition
        return await self.getTuitionByIdAsync(tuition_id)
