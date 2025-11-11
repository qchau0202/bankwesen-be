"""
Initialize tuition_db with sample data for testing.
Uses UTC+7 timezone for all datetime fields.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Define UTC+7 timezone
UTC_PLUS_7 = timezone(timedelta(hours=7))

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "tuition_db"


async def init_database():
    """Initialize tuition database with sample students and tuition records."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print(f"🔄 Initializing {DATABASE_NAME}...")
    
    # Clear existing data (optional - comment out in production)
    await db.Student.delete_many({})
    await db.Tuition.delete_many({})
    print("✅ Cleared existing data")
    
    # Sample Students
    now_utc7 = datetime.now(UTC_PLUS_7)
    students = [
        {
            "studentid": "ST1731369600",
            "student_name": "John Doe",
            "student_code": "523K0001",
            "email": "john.doe@student.edu",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "studentid": "ST1731369601",
            "student_name": "Jane Smith",
            "student_code": "523K0002",
            "email": "jane.smith@student.edu",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "studentid": "ST1731369602",
            "student_name": "Bob Johnson",
            "student_code": "523K0003",
            "email": "bob.johnson@student.edu",
            "created_at": now_utc7,
            "updated_at": now_utc7
        }
    ]
    
    result = await db.Student.insert_many(students)
    print(f"✅ Inserted {len(result.inserted_ids)} students")
    
    # Sample Tuition Records
    tuitions = [
        {
            "tuitionid": "TU1731369600001",
            "studentid": "ST1731369600",
            "semester": "Semester I",
            "year": "2023-2024",
            "tuition_ammount": 5000.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600002",
            "studentid": "ST1731369600",
            "semester": "Semester II",
            "year": "2023-2024",
            "tuition_ammount": 5000.00,
            "due_date": now_utc7 + timedelta(days=150),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600003",
            "studentid": "ST1731369601",
            "semester": "Semester I",
            "year": "2023-2024",
            "tuition_ammount": 4800.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600004",
            "studentid": "ST1731369602",
            "semester": "Summer Semester",
            "year": "2023-2024",
            "tuition_ammount": 5200.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "paid",
            "created_at": now_utc7
        }
    ]
    
    result = await db.Tuition.insert_many(tuitions)
    print(f"✅ Inserted {len(result.inserted_ids)} tuition records")
    
    # Create indexes
    await db.Student.create_index("studentid", unique=True)
    await db.Tuition.create_index("tuitionid", unique=True)
    await db.Tuition.create_index("studentid")
    print("✅ Created indexes")
    
    # Display summary
    student_count = await db.Student.count_documents({})
    tuition_count = await db.Tuition.count_documents({})
    
    print(f"\n📊 Database Summary:")
    print(f"   Students: {student_count}")
    print(f"   Tuition Records: {tuition_count}")
    
    client.close()
    print(f"\n✅ {DATABASE_NAME} initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())
