from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.tuition import TuitionModel
from app.schemas.tuition import TuitionResponse, StudentTuitionListResponse
from fastapi import HTTPException
from datetime import datetime


class TuitionService:
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.tuitions
    
    def _formatCurrency(self, amount: float) -> str:
        return f"{amount:,.0f} VND"
    
    async def getStudentTuitionsAsync(
        self, 
        student_id: str, 
        academic_year: Optional[str] = None, 
        semester: Optional[str] = None
    ) -> StudentTuitionListResponse:
        # Build query with filters (case-insensitive)
        query = {"studentId": {"$regex": f"^{student_id}$", "$options": "i"}}
        
        if academic_year:
            query["academic_year"] = {"$regex": f"^{academic_year}$", "$options": "i"}
        
        if semester:
            query["semester"] = {"$regex": f"^{semester}$", "$options": "i"}
        
        # Fetch all tuition records for the student
        cursor = self.collection.find(query)
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
                status=tuition_doc.get("status", "debt"),
                created_at=tuition_doc.get("created_at", datetime.utcnow())
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
        tuition_doc = await self.collection.find_one({"tuitionId": {"$regex": f"^{tuition_id}$", "$options": "i"}})
        
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
            status=tuition_doc.get("status", "debt"),
            created_at=tuition_doc.get("created_at", datetime.utcnow())
        )
    
    async def updateTuitionStatusAsync(self, tuition_id: str, status: str) -> TuitionResponse:
        # Validate status
        valid_statuses = ["debt", "paid"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if tuition exists (case-insensitive)
        tuition_doc = await self.collection.find_one({"tuitionId": {"$regex": f"^{tuition_id}$", "$options": "i"}})
        if not tuition_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Tuition record not found: {tuition_id}"
            )
        
        # Update the tuition record (case-insensitive)
        result = await self.collection.update_one(
            {"tuitionId": {"$regex": f"^{tuition_id}$", "$options": "i"}},
            {"$set": {
                "status": status
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to update tuition status"
            )
        
        # Return updated tuition
        return await self.getTuitionByIdAsync(tuition_id)
