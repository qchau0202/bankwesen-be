"""
Initialize payment_db with sample data for testing.
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
DATABASE_NAME = "payment_db"


async def init_database():
    """Initialize payment database with sample payment records."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print(f"🔄 Initializing {DATABASE_NAME}...")
    
    # Clear existing data (optional - comment out in production)
    await db.Payment.delete_many({})
    print("✅ Cleared existing data")
    
    # Sample Payment Records
    now_utc7 = datetime.now(UTC_PLUS_7)
    payments = [
        {
            "paymentid": "PAY1731369600001",
            "studentid": "ST1731369600",
            "idempotency_key": "idempotency-key-001",
            "userid": "ST1731369600",
            "tuitionid": "TU1731369600001",
            "ammount": 5000.00,
            "status": "completed",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "paymentid": "PAY1731369600002",
            "studentid": "ST1731369601",
            "idempotency_key": "idempotency-key-002",
            "userid": "ST1731369601",
            "tuitionid": "TU1731369600003",
            "ammount": 2400.00,
            "status": "completed",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "paymentid": "PAY1731369600003",
            "studentid": "ST1731369602",
            "idempotency_key": "idempotency-key-003",
            "userid": "ST1731369602",
            "tuitionid": "TU1731369600004",
            "ammount": 5200.00,
            "status": "completed",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "paymentid": "PAY1731369600004",
            "studentid": "ST1731369600",
            "idempotency_key": "idempotency-key-004",
            "userid": "ST1731369600",
            "tuitionid": "TU1731369600002",
            "ammount": 1000.00,
            "status": "pending",
            "created_at": now_utc7,
            "updated_at": now_utc7
        }
    ]
    
    result = await db.Payment.insert_many(payments)
    print(f"✅ Inserted {len(result.inserted_ids)} payment records")
    
    # Create indexes
    await db.Payment.create_index("paymentid", unique=True)
    await db.Payment.create_index("idempotency_key", unique=True)
    await db.Payment.create_index("studentid")
    await db.Payment.create_index("userid")
    await db.Payment.create_index("tuitionid")
    print("✅ Created indexes")
    
    # Display summary
    payment_count = await db.Payment.count_documents({})
    completed_payments = await db.Payment.count_documents({"status": "completed"})
    pending_payments = await db.Payment.count_documents({"status": "pending"})
    
    print(f"\n📊 Database Summary:")
    print(f"   Total Payments: {payment_count}")
    print(f"   Completed: {completed_payments}")
    print(f"   Pending: {pending_payments}")
    
    client.close()
    print(f"\n✅ {DATABASE_NAME} initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())
