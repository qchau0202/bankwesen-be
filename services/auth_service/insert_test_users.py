"""
Script to insert test users into MongoDB with hashed passwords.
This script creates sample users with different roles for testing the authentication system.
Passwords are securely hashed using bcrypt before storing in the database.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB configuration from environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auth_db")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "User")

# Validate MongoDB URL is loaded
if not MONGODB_URL:
    raise ValueError("MONGODB_URL not found in environment variables. Please check your .env file.")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def insert_test_users():
    """Insert test users into MongoDB."""
    
    print(f"Connecting to MongoDB...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {USERS_COLLECTION}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        MONGODB_URL,
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
            "customerid": "523K0013",
            "username": "student1",
            "password_hash": hash_password("password123"),
            "full_name": "Duong Thanh Long",
            "email": "thanhlongduong6a3@gmail.com",
            "phone_number": "0905877708",
            "balance": 50000000.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "customerid": "523K0002",
            "username": "student2",
            "password_hash": hash_password("password123"),
            "full_name": "Le Huu Thanh",
            "email": "duongthanhlong220805@gmail.com",
            "phone_number": "0387504809",
            "balance": 10000000.0,
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
            print(f"   ✅ Inserted user: {user['username']} (ID: {result.inserted_id})")
    
    # Display summary
    print("\n" + "="*80)
    print("📊 TEST USERS SUMMARY")
    print("="*80)
    
    all_users = await users_collection.find({}).to_list(length=100)
    
    for user in all_users:
        print(f"\n👤 {user['full_name']}")
        print(f"   Username: {user['username']}")
        print(f"   User ID:  {user['userid']}")
        print(f"   Email:    {user['email']}")
        print(f"   Balance:  ${user['balance']:.2f}")
    
    print("\n" + "="*80)
    print("🔑 LOGIN CREDENTIALS FOR TESTING")
    print("="*80)
    print("\n👤 User Accounts:")
    print("   Username: student1  |  Password: password123")
    print("   Username: student2  |  Password: password123")
    print("="*80)
    
    # Close connection
    client.close()
    print("\n✅ MongoDB connection closed")
    print("✅ Test users inserted successfully!")


if __name__ == "__main__":
    asyncio.run(insert_test_users())
