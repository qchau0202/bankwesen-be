"""
Insert sample student tuition data into tuition_db.
This script creates sample tuition records for testing purposes.
All amounts are in Vietnamese Dong (VND).
Uses UTC+7 timezone for datetime fields.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Define UTC+7 timezone (Vietnam timezone)
UTC_PLUS_7 = timezone(timedelta(hours=7))

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tuition_db")


async def insert_sample_tuition():
    """Insert sample tuition records with student information."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print(f"Inserting sample data into {DATABASE_NAME}...")
    
    result = await db.tuitions.delete_many({})
    print(f"Cleared {result.deleted_count} existing records")
    
    now_utc7 = datetime.now(UTC_PLUS_7)
    
    sample_tuitions = [
        {
            "tuitionId": "TU2024110001",
            "studentId": "523K0001",
            "studentName": "Ly Hung Quoc Chau",
            "studentEmail": "quocchau4729@gmail.com",
            "semester": "Semester I",
            "academic_year": "2022-2023",
            "tuition_amount": 14000000.00,  # 14 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=750)
        },
        {
            "tuitionId": "TU2024110002",
            "studentId": "523K0001",
            "studentName": "Ly Hung Quoc Chau",
            "studentEmail": "quocchau4729@gmail.com",
            "semester": "Semester II",
            "academic_year": "2022-2023",
            "tuition_amount": 14000000.00,  # 14 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=600)
        },
        {
            "tuitionId": "TU2024110003",
            "studentId": "523K0001",
            "studentName": "Ly Hung Quoc Chau",
            "studentEmail": "quocchau4729@gmail.com",
            "semester": "Semester I",
            "academic_year": "2023-2024",
            "tuition_amount": 15000000.00,  # 15 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=450)
        },
        {
            "tuitionId": "TU2024110004",
            "studentId": "523K0001",
            "studentName": "Ly Hung Quoc Chau",
            "studentEmail": "quocchau4729@gmail.com",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 15000000.00,  # 15 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=300)
        },
        {
            "tuitionId": "TU2024110005",
            "studentId": "523K0001",
            "studentName": "Ly Hung Quoc Chau",
            "studentEmail": "quocchau4729@gmail.com",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 16000000.00,  # 16 million VND
            "status": "debt",
            "created_at": now_utc7
        },
        
        # Student 2: Tran Thi B - All previous years paid, current year unpaid
        {
            "tuitionId": "TU2024110006",
            "studentId": "523K0002",
            "studentName": "Tran Thi B",
            "studentEmail": "tranthib@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2023-2024",
            "tuition_amount": 17000000.00,  # 17 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=450)
        },
        {
            "tuitionId": "TU2024110007",
            "studentId": "523K0002",
            "studentName": "Tran Thi B",
            "studentEmail": "tranthib@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 17000000.00,  # 17 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=300)
        },
        {
            "tuitionId": "TU2024110008",
            "studentId": "523K0002",
            "studentName": "Tran Thi B",
            "studentEmail": "tranthib@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 18000000.00,  # 18 million VND
            "status": "debt",
            "created_at": now_utc7
        },
        
        # Student 3: Le Van C - All paid up to current semester
        {
            "tuitionId": "TU2024110009",
            "studentId": "523K0003",
            "studentName": "Le Van C",
            "studentEmail": "levanc@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 16000000.00,  # 16 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=300)
        },
        {
            "tuitionId": "TU2024110010",
            "studentId": "523K0003",
            "studentName": "Le Van C",
            "studentEmail": "levanc@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 16500000.00,  # 16.5 million VND
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=10)
        },
        
        # Student 4: Pham Thi D - New student with current year debt
        {
            "tuitionId": "TU2024110011",
            "studentId": "523K0004",
            "studentName": "Pham Thi D",
            "studentEmail": "phamthid@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 20000000.00,  # 20 million VND (international program)
            "status": "debt",
            "created_at": now_utc7
        },
        
        # Student 5: Hoang Van E - Has unpaid fees from BOTH old and current year
        # When paying, MUST pay all unpaid fees together
        {
            "tuitionId": "TU2024110012",
            "studentId": "523K0005",
            "studentName": "Hoang Van E",
            "studentEmail": "hoangvane@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2023-2024",
            "tuition_amount": 14000000.00,  # 14 million VND
            "status": "debt",  # Old debt - must be paid first
            "created_at": now_utc7 - timedelta(days=450)
        },
        {
            "tuitionId": "TU2024110013",
            "studentId": "523K0005",
            "studentName": "Hoang Van E",
            "studentEmail": "hoangvane@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 14000000.00,  # 14 million VND
            "status": "debt",  # Old debt - must be paid with above
            "created_at": now_utc7 - timedelta(days=300)
        },
        {
            "tuitionId": "TU2024110014",
            "studentId": "523K0005",
            "studentName": "Hoang Van E",
            "studentEmail": "hoangvane@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 15000000.00,  # 15 million VND
            "status": "debt",
            "created_at": now_utc7
        }
    ]
    
    # Insert all sample records
    result = await db.tuitions.insert_many(sample_tuitions)
    print(f"Inserted {len(result.inserted_ids)} tuition records")
    
    await db.tuitions.create_index("tuitionId", unique=True)
    await db.tuitions.create_index("studentId")
    await db.tuitions.create_index([("studentId", 1), ("academic_year", -1)])
    print("Created indexes")
    
    # Display summary statistics
    total_records = await db.tuitions.count_documents({})
    debt_records = await db.tuitions.count_documents({"status": "debt"})
    paid_records = await db.tuitions.count_documents({"status": "paid"})
    partial_records = await db.tuitions.count_documents({"status": "partial"})
    
    # Calculate total amounts
    pipeline = [
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$tuition_amount"}
        }}
    ]
    amounts_by_status = await db.tuitions.aggregate(pipeline).to_list(None)
    
    print(f"\nDatabase Summary:")
    print(f"   Total Tuition Records: {total_records}")
    print(f"   - debt: {debt_records}")
    print(f"   - Paid: {paid_records}")
    print(f"   - Partial: {partial_records}")
    print(f"\nAmounts by Status (VND):")
    for item in amounts_by_status:
        status = item['_id']
        total = item['total']
        print(f"   - {status.capitalize()}: {total:,.0f} VND")
    
    unique_students = await db.tuitions.distinct("studentId")
    print(f"\nNumber of Students: {len(unique_students)}")
    print(f"   Student IDs: {', '.join(unique_students)}")
    
    client.close()
    print(f"\nSample data insertion complete!")
    print(f"\nYou can now test the API:")
    print(f"   GET /api/tuition/{{studentId}} - e.g., GET /api/tuition/523K0001")
    print(f"   GET /api/tuition/record/{{tuitionId}} - e.g., GET /api/tuition/record/TU2024110001")


if __name__ == "__main__":
    asyncio.run(insert_sample_tuition())
