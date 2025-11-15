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
    
    print(f"🔄 Inserting sample data into {DATABASE_NAME}...")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    result = await db.Tuition.delete_many({})
    print(f"✅ Cleared {result.deleted_count} existing records")
    
    # Current time in UTC+7
    now_utc7 = datetime.now(UTC_PLUS_7)
    
    # Sample tuition records with realistic Vietnamese student data
    # Currency: Vietnamese Dong (VND)
    # Typical university tuition: 10-20 million VND per semester
    sample_tuitions = [
        # Student 1: Nguyen Van A - Multiple semesters
        {
            "tuitionId": "TU2024110001",
            "studentId": "523K0001",
            "studentName": "Nguyen Van A",
            "studentEmail": "nguyenvana@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 15000000.00,  # 15 million VND
            "due_date": now_utc7 + timedelta(days=30),
            "status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionId": "TU2024110002",
            "studentId": "523K0001",
            "studentName": "Nguyen Van A",
            "studentEmail": "nguyenvana@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 15000000.00,  # 15 million VND
            "due_date": now_utc7 - timedelta(days=30),
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=150)
        },
        {
            "tuitionId": "TU2024110003",
            "studentId": "523K0001",
            "studentName": "Nguyen Van A",
            "studentEmail": "nguyenvana@student.edu.vn",
            "semester": "Summer Semester",
            "academic_year": "2024-2025",
            "tuition_amount": 8000000.00,  # 8 million VND (summer is usually cheaper)
            "due_date": now_utc7 + timedelta(days=60),
            "status": "pending",
            "created_at": now_utc7
        },
        
        # Student 2: Tran Thi B - Different status
        {
            "tuitionId": "TU2024110004",
            "studentId": "523K0002",
            "studentName": "Tran Thi B",
            "studentEmail": "tranthib@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 18000000.00,  # 18 million VND
            "due_date": now_utc7 + timedelta(days=45),
            "status": "partial",
            "created_at": now_utc7
        },
        {
            "tuitionId": "TU2024110005",
            "studentId": "523K0002",
            "studentName": "Tran Thi B",
            "studentEmail": "tranthib@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2023-2024",
            "tuition_amount": 17000000.00,  # 17 million VND
            "due_date": now_utc7 - timedelta(days=60),
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=200)
        },
        
        # Student 3: Le Van C - All paid
        {
            "tuitionId": "TU2024110006",
            "studentId": "523K0003",
            "studentName": "Le Van C",
            "studentEmail": "levanc@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 16000000.00,  # 16 million VND
            "due_date": now_utc7 - timedelta(days=90),
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=180)
        },
        {
            "tuitionId": "TU2024110007",
            "studentId": "523K0003",
            "studentName": "Le Van C",
            "studentEmail": "levanc@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 16500000.00,  # 16.5 million VND
            "due_date": now_utc7 + timedelta(days=20),
            "status": "paid",
            "created_at": now_utc7 - timedelta(days=10)
        },
        
        # Student 4: Pham Thi D - New student with pending payment
        {
            "tuitionId": "TU2024110008",
            "studentId": "523K0004",
            "studentName": "Pham Thi D",
            "studentEmail": "phamthid@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 20000000.00,  # 20 million VND (international program)
            "due_date": now_utc7 + timedelta(days=15),
            "status": "pending",
            "created_at": now_utc7
        },
        
        # Student 5: Hoang Van E - Overdue payment
        {
            "tuitionId": "TU2024110009",
            "studentId": "523K0005",
            "studentName": "Hoang Van E",
            "studentEmail": "hoangvane@student.edu.vn",
            "semester": "Semester II",
            "academic_year": "2023-2024",
            "tuition_amount": 14000000.00,  # 14 million VND
            "due_date": now_utc7 - timedelta(days=15),
            "status": "pending",
            "created_at": now_utc7 - timedelta(days=150)
        },
        {
            "tuitionId": "TU2024110010",
            "studentId": "523K0005",
            "studentName": "Hoang Van E",
            "studentEmail": "hoangvane@student.edu.vn",
            "semester": "Semester I",
            "academic_year": "2024-2025",
            "tuition_amount": 14500000.00,  # 14.5 million VND
            "due_date": now_utc7 + timedelta(days=25),
            "status": "pending",
            "created_at": now_utc7
        }
    ]
    
    # Insert all sample records
    result = await db.Tuition.insert_many(sample_tuitions)
    print(f"✅ Inserted {len(result.inserted_ids)} tuition records")
    
    # Create indexes for better query performance
    await db.Tuition.create_index("tuitionId", unique=True)
    await db.Tuition.create_index("studentId")
    await db.Tuition.create_index([("studentId", 1), ("academic_year", -1)])
    print("✅ Created indexes")
    
    # Display summary statistics
    total_records = await db.Tuition.count_documents({})
    pending_records = await db.Tuition.count_documents({"status": "pending"})
    paid_records = await db.Tuition.count_documents({"status": "paid"})
    partial_records = await db.Tuition.count_documents({"status": "partial"})
    
    # Calculate total amounts
    pipeline = [
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$tuition_amount"}
        }}
    ]
    amounts_by_status = await db.Tuition.aggregate(pipeline).to_list(None)
    
    print(f"\n📊 Database Summary:")
    print(f"   Total Tuition Records: {total_records}")
    print(f"   - Pending: {pending_records}")
    print(f"   - Paid: {paid_records}")
    print(f"   - Partial: {partial_records}")
    print(f"\n💰 Amounts by Status (VND):")
    for item in amounts_by_status:
        status = item['_id']
        total = item['total']
        print(f"   - {status.capitalize()}: {total:,.0f} VND")
    
    # List unique students
    unique_students = await db.Tuition.distinct("studentId")
    print(f"\n👥 Number of Students: {len(unique_students)}")
    print(f"   Student IDs: {', '.join(unique_students)}")
    
    client.close()
    print(f"\n✅ Sample data insertion complete!")
    print(f"\n💡 You can now test the API:")
    print(f"   GET /api/tuition/{{studentId}} - e.g., GET /api/tuition/523K0001")
    print(f"   GET /api/tuition/record/{{tuitionId}} - e.g., GET /api/tuition/record/TU2024110001")


if __name__ == "__main__":
    asyncio.run(insert_sample_tuition())
