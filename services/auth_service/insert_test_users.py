"""
Script to insert test users into MongoDB with hashed passwords.
This script creates sample users with different roles for testing the authentication system.
Passwords are securely hashed using bcrypt before storing in the database.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
from dotenv import load_dotenv
import certifi

# Load environment variables from .env file
load_dotenv()

# MongoDB configuration from environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auth_db")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "User")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Validate MongoDB URL is loaded
if not MONGODB_URL:
    raise ValueError("MONGODB_URL not found in environment variables. Please check your .env file.")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


async def insert_test_users():
    """Insert test users into MongoDB."""
    
    print(f"Connecting to MongoDB...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {USERS_COLLECTION}")
    
    # Connect to MongoDB with SSL certificate
    client = AsyncIOMotorClient(
        MONGODB_URL,
        tlsCAFile=certifi.where(),  # Use certifi for SSL certificates
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    db = client[DATABASE_NAME]
    users_collection = db[USERS_COLLECTION]
    print("✅ Connected successfully!")
    
    # Define test users with hashed passwords
    test_users = [
        {
            "userid": "523K0001",
            "username": "student1",
            "password_hash": hash_password("password123"),
            "role": "student",
            "full_name": "John Doe",
            "email": "john.doe@university.edu",
            "balance": 5000.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "userid": "523K0002",
            "username": "student2",
            "password_hash": hash_password("password123"),
            "role": "student",
            "full_name": "Jane Smith",
            "email": "jane.smith@university.edu",
            "balance": 3000.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "userid": "523K0002",
            "username": "staff1",
            "password_hash": hash_password("staff123"),
            "role": "staff",
            "full_name": "Alice Johnson",
            "email": "alice.johnson@university.edu",
            "balance": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "userid": "AD001",
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "full_name": "Admin User",
            "email": "admin@university.edu",
            "balance": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Clear existing users (optional - comment out if you want to keep existing data)
    print("\n🗑️  Clearing existing users...")
    delete_result = await users_collection.delete_many({})
    print(f"   Deleted {delete_result.deleted_count} existing users")
    
    # Insert test users
    print("\n📝 Inserting test users...")
    for user in test_users:
        # Check if user already exists
        existing_user = await users_collection.find_one({"username": user["username"]})
        
        if existing_user:
            print(f"   ⚠️  User '{user['username']}' already exists, skipping...")
        else:
            result = await users_collection.insert_one(user)
            print(f"   ✅ Inserted user: {user['username']} (Role: {user['role']}, ID: {result.inserted_id})")
    
    # Display summary
    print("\n" + "="*80)
    print("📊 TEST USERS SUMMARY")
    print("="*80)
    
    all_users = await users_collection.find({}).to_list(length=100)
    
    for user in all_users:
        print(f"\n👤 {user['full_name']}")
        print(f"   Username: {user['username']}")
        print(f"   User ID:  {user['userid']}")
        print(f"   Role:     {user['role']}")
        print(f"   Email:    {user['email']}")
        print(f"   Balance:  ${user['balance']:.2f}")
    
    print("\n" + "="*80)
    print("🔑 LOGIN CREDENTIALS FOR TESTING")
    print("="*80)
    print("\n📚 Student Accounts:")
    print("   Username: student1  |  Password: password123")
    print("   Username: student2  |  Password: password123")
    print("\n👔 Staff Account:")
    print("   Username: staff1    |  Password: staff123")
    print("\n🔐 Admin Account:")
    print("   Username: admin     |  Password: admin123")
    print("="*80)
    
    # Close connection
    client.close()
    print("\n✅ MongoDB connection closed")
    print("✅ Test users inserted successfully!")


if __name__ == "__main__":
    asyncio.run(insert_test_users())
