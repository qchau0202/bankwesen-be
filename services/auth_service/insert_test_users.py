"""
Script to insert test users into MongoDB with hashed passwords.
This script creates sample users with different roles for testing the authentication system.
Passwords are securely hashed using bcrypt before storing in the database.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import certifi
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB configuration from environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auth_db")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")

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
    
    # Connect to MongoDB with SSL certificate handling for Atlas
    client = AsyncIOMotorClient(
        MONGODB_URL,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    # Test connection first
    try:
        await client.admin.command('ping')
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection test failed: {e}")
        client.close()
        raise
    
    db = client[DATABASE_NAME]
    users_collection = db[USERS_COLLECTION]
    
    # Define test users with hashed passwords
    test_users = [
        {
            "customerId": "523K0013",
            "username": "student1",
            "password_hash": hash_password("password123"),
            "full_name": "Duong Thanh Long",
            "email": "thanhlongduong6a3@gmail.com",
            "phone_number": "0905877708",
            "balance": 50000000.0,
            "payment_history": [],
            "created_at": datetime.utcnow()
        },
        {
            "customerId": "523K0001",
            "username": "student2",
            "password_hash": hash_password("password123"),
            "full_name": "Ly Hung Quoc Chau",
            "email": "duongthanhlong220805@gmail.com",
            "phone_number": "0387504809",
            "balance": 10000000.0,
            "payment_history": [],
            "created_at": datetime.utcnow()
        }
    ]
    
    # Insert test users
    print("\nInserting test users...")
    for user in test_users:
        # Check if user already exists by username or customerId
        existing_user = await users_collection.find_one({
            "$or": [
                {"username": user["username"]},
                {"customerId": user["customerId"]}
            ]
        })
        
        if existing_user:
            print(f"   User '{user['username']}' (customerId: {user['customerId']}) already exists, skipping...")
        else:
            try:
                result = await users_collection.insert_one(user)
                print(f"   Inserted user: {user['username']} (ID: {result.inserted_id})")
            except Exception as e:
                print(f"   Error inserting user '{user['username']}': {str(e)}")
    
    # Display summary
    print("\n" + "="*80)
    print("TEST USERS SUMMARY")
    print("="*80)
    
    all_users = await users_collection.find({}).to_list(length=100)
    
    for user in all_users:
        print(f"\n{user['full_name']}")
        print(f"   Username: {user['username']}")
        print(f"   Customer ID:  {user.get('customerId', 'N/A')}")
        print(f"   Phone Number: {user['phone_number']}")
        print(f"   Email:    {user['email']}")
        print(f"   Balance:  ${user['balance']:.2f}")
    
    print("\n" + "="*80)
    print("LOGIN CREDENTIALS FOR TESTING")
    print("="*80)
    print("\nUser Accounts:")
    print("   Username: student1  |  Password: 123456")
    print("   Username: student2  |  Password: 123456")
    print("="*80)
    
    # Close connection
    client.close()
    print("\nMongoDB connection closed")
    print("Test users inserted successfully!")


if __name__ == "__main__":
    asyncio.run(insert_test_users())
