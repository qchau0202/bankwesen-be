from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import certifi
from ..core.config import settings

# Global MongoDB client
mongodb_client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongodb():
    """Connect to MongoDB with SSL certificate handling."""
    global mongodb_client
    try:
        # Initialize client
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )

        # Test connection first
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")

        # Assign to global only if success
        mongodb_client = client

    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        print("⚠️  Warning: MongoDB connection failed. API will work but database operations will fail.")
        mongodb_client = None  # ensure it’s explicitly None


async def close_mongodb_connection():
    """Close MongoDB connection."""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        mongodb_client = None
        print("✅ MongoDB connection closed")


def get_database():
    """Get the database instance."""
    if not mongodb_client:
        raise Exception("Database not connected")
    return mongodb_client[settings.DATABASE_NAME]


def get_users_collection():
    """Get the users collection."""
    db = get_database()
    return db[settings.USERS_COLLECTION]
