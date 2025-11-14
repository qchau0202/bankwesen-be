"""
Initialize all databases for the Bankwesen microservices project.
This script sets up auth_db, tuition_db, and payment_db with sample data.
Uses UTC+7 timezone for all datetime fields.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Define UTC+7 timezone
UTC_PLUS_7 = timezone(timedelta(hours=7))

# Add service directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'auth_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'tuition_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'payment_service'))


async def init_auth_db():
    """Initialize auth database."""
    print("\n" + "="*60)
    print("1. INITIALIZING AUTH_DB")
    print("="*60)
    
    # Import here to avoid module conflicts
    from motor.motor_asyncio import AsyncIOMotorClient
    from passlib.context import CryptContext
    from dotenv import load_dotenv
    
    load_dotenv('services/auth_service/.env')
    
    MONGODB_URL = os.getenv("MONGODB_URL")
    DATABASE_NAME = "auth_db"
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Clear existing
    await db.User.delete_many({})
    
    # Create test users
    now_utc7 = datetime.now(UTC_PLUS_7)
    users = [
        {
            "userid": "ST1731369600",
            "username": "student1",
            "password_hash": pwd_context.hash("password123"),
            "role": "student",
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone_number": "1234567890",
            "balance": 1000.0,
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "userid": "ST1731369601",
            "username": "student2",
            "password_hash": pwd_context.hash("password123"),
            "role": "student",
            "full_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone_number": "0987654321",
            "balance": 500.0,
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "userid": "ST1731369602",
            "username": "student3",
            "password_hash": pwd_context.hash("password123"),
            "role": "student",
            "full_name": "Bob Johnson",
            "email": "bob.johnson@example.com",
            "phone_number": "5551234567",
            "balance": 2000.0,
            "created_at": now_utc7,
            "updated_at": now_utc7
        }
    ]
    
    result = await db.User.insert_many(users)
    print(f"✅ Inserted {len(result.inserted_ids)} users")
    
    # Create indexes
    await db.User.create_index("userid", unique=True)
    await db.User.create_index("username", unique=True)
    await db.User.create_index("email", unique=True)
    
    count = await db.User.count_documents({})
    print(f"📊 Total users: {count}")
    
    client.close()


async def init_tuition_db():
    """Initialize tuition database."""
    print("\n" + "="*60)
    print("2. INITIALIZING TUITION_DB")
    print("="*60)
    
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    
    load_dotenv('services/tuition_service/.env')
    
    MONGODB_URL = os.getenv("MONGODB_URL")
    DATABASE_NAME = "tuition_db"
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Clear existing
    await db.Tuition.delete_many({})
    
    # Create tuitions (now includes student info)
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
            "studentname": "Jane Smith",
            "studentcode": "523K0002",
            "studentemail": "jane.smith@student.edu",
            "semester": "Semester II",
            "year": "2023-2024",
            "tuition_ammount": 4800.00,
            "due_date": now_utc7 + timedelta(days=30),
            "payment_status": "pending",
            "created_at": now_utc7
        },
        {
            "tuitionid": "TU1731369600003",
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
    await db.Tuition.create_index("tuitionid", unique=True)
    await db.Tuition.create_index("studentcode")
    
    tuition_count = await db.Tuition.count_documents({})
    print(f"📊 Tuitions: {tuition_count}")
    
    client.close()


async def init_payment_db():
    """Initialize payment database."""
    print("\n" + "="*60)
    print("3. INITIALIZING PAYMENT_DB")
    print("="*60)
    
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    
    load_dotenv('services/payment_service/.env')
    
    MONGODB_URL = os.getenv("MONGODB_URL")
    DATABASE_NAME = "payment_db"
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Clear existing
    await db.Payment.delete_many({})
    
    # Create payments
    now_utc7 = datetime.now(UTC_PLUS_7)
    payments = [
        {
            "paymentid": "PAY1731369600001",
            "studentid": "ST1731369602",
            "idempotency_key": "idempotency-key-001",
            "userid": "ST1731369602",
            "tuitionid": "TU1731369600003",
            "ammount": 5200.00,
            "status": "completed",
            "created_at": now_utc7,
            "updated_at": now_utc7
        },
        {
            "paymentid": "PAY1731369600002",
            "studentid": "ST1731369600",
            "idempotency_key": "idempotency-key-002",
            "userid": "ST1731369600",
            "tuitionid": "TU1731369600001",
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
    
    payment_count = await db.Payment.count_documents({})
    completed = await db.Payment.count_documents({"status": "completed"})
    pending = await db.Payment.count_documents({"status": "pending"})
    print(f"📊 Payments: {payment_count} (Completed: {completed}, Pending: {pending})")
    
    client.close()


async def main():
    """Initialize all databases."""
    print("\n" + "🚀 "+"="*56 + " 🚀")
    print("  BANKWESEN MICROSERVICES - DATABASE INITIALIZATION")
    print("🚀 " + "="*56 + " 🚀")
    
    try:
        await init_auth_db()
        await init_tuition_db()
        await init_payment_db()
        
        print("\n" + "="*60)
        print("✅ ALL DATABASES INITIALIZED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 Summary:")
        print("   - auth_db: User authentication")
        print("   - tuition_db: Students and tuition records")
        print("   - payment_db: Payment transactions")
        print("\n🔗 Next steps:")
        print("   1. Start services: docker-compose up -d")
        print("   2. Check status: docker-compose ps")
        print("   3. View logs: docker-compose logs -f")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
