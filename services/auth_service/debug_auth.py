"""
Debug script to check database users and test password verification
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auth_db")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "User")

# Password hashing context (same as in security.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def debug_users():
    """Debug users in database."""
    
    print("="*80)
    print("🔍 DEBUGGING AUTH SERVICE")
    print("="*80)
    
    # Connect to MongoDB
    print(f"\n📡 Connecting to MongoDB...")
    print(f"   Database: {DATABASE_NAME}")
    print(f"   Collection: {USERS_COLLECTION}")
    
    client = AsyncIOMotorClient(
        MONGODB_URL,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    db = client[DATABASE_NAME]
    users_collection = db[USERS_COLLECTION]
    print("   ✅ Connected!\n")
    
    # Fetch all users
    users = await users_collection.find({}).to_list(length=100)
    
    if not users:
        print("❌ No users found in database!")
        print("   Run: python insert_test_users.py")
        return
    
    print(f"📊 Found {len(users)} users in database:\n")
    
    # Display each user
    for i, user in enumerate(users, 1):
        print(f"User {i}:")
        print(f"   Username: {user.get('username')}")
        print(f"   User ID:  {user.get('userid')}")
        print(f"   Role:     {user.get('role')}")
        
        # Check which password field exists
        has_password = 'password' in user
        has_password_hash = 'password_hash' in user
        
        if has_password:
            print(f"   ⚠️  Has 'password' field (PLAIN TEXT): {user['password'][:20]}...")
        if has_password_hash:
            print(f"   ✅ Has 'password_hash' field (HASHED): {user['password_hash'][:50]}...")
        
        if not has_password and not has_password_hash:
            print(f"   ❌ NO PASSWORD FIELD FOUND!")
        
        print()
    
    # Test password verification
    print("\n" + "="*80)
    print("🧪 TESTING PASSWORD VERIFICATION")
    print("="*80)
    
    test_user = await users_collection.find_one({"username": "student1"})
    
    if test_user:
        print(f"\n✅ Found user 'student1'")
        
        # Check password field
        if 'password_hash' in test_user:
            password_hash = test_user['password_hash']
            print(f"   Password Hash: {password_hash[:50]}...")
            
            # Test verification
            test_password = "password123"
            print(f"\n   Testing password: '{test_password}'")
            
            try:
                is_valid = pwd_context.verify(test_password, password_hash)
                if is_valid:
                    print(f"   ✅ Password verification SUCCESS!")
                else:
                    print(f"   ❌ Password verification FAILED!")
            except Exception as e:
                print(f"   ❌ Error during verification: {e}")
        
        elif 'password' in test_user:
            print(f"   ⚠️  User has PLAIN PASSWORD field: {test_user['password']}")
            print(f"   ❌ This is the OLD format - need to re-run insert_test_users.py!")
        else:
            print(f"   ❌ No password field found!")
    else:
        print("\n❌ User 'student1' not found!")
    
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    # Check if any user has plain password
    users_with_plain_password = [u for u in users if 'password' in u and 'password_hash' not in u]
    users_with_hash = [u for u in users if 'password_hash' in u]
    
    if users_with_plain_password:
        print("\n⚠️  WARNING: Some users have PLAIN passwords!")
        print("   Run this command to fix:")
        print("   python insert_test_users.py")
    
    if users_with_hash:
        print(f"\n✅ {len(users_with_hash)} users have properly hashed passwords")
    
    # Close connection
    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(debug_users())
