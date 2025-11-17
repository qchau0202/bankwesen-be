from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# MongoDB client
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    print(f"Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database():
    """Get database instance."""
    return database
