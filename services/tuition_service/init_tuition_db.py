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
    await db.Tuition.delete_many({})
    print("✅ Cleared existing data")
    
    # Sample Tuition Records (now includes student info)
    now_utc7 = datetime.now(UTC_PLUS_7)
    tuitions = [
        {
            "tuitionid": "TU1731369600001",
            "studentname": "John Doe",
            "studentcode": "523K0001",
            "studentemail": "john.doe@student.edu",
            "semester": "Semester I",
            "year": "2023-2024",
            "tuition_ammount": 5000.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600002",
            "studentname": "John Doe",
            "studentcode": "523K0001",
            "studentemail": "john.doe@student.edu",
            "semester": "Semester II",
            "year": "2023-2024",
            "tuition_ammount": 5000.00,
            "due_date": now_utc7 + timedelta(days=150),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600003",
            "studentname": "Jane Smith",
            "studentcode": "523K0002",
            "studentemail": "jane.smith@student.edu",
            "semester": "Semester I",
            "year": "2023-2024",
            "tuition_ammount": 4800.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600004",
            "studentname": "Bob Johnson",
            "studentcode": "523K0003",
            "studentemail": "bob.johnson@student.edu",
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
