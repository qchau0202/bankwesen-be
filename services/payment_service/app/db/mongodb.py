from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# MongoDB client
client: AsyncIOMotorClient = None
database = None
auth_database = None
tuition_database = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, database, auth_database, tuition_database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    auth_database = client[settings.AUTH_DATABASE_NAME]
    tuition_database = client[settings.TUITION_DATABASE_NAME]
    
    # Create indexes for payment collection
    payments_collection = database["payments"]
    
    # Create index on tuitionIds array for faster lookups
    # Note: We check for conflicts in application code since payments can have multiple tuition IDs
    await payments_collection.create_index([("tuitionIds", 1)])
    
    # Create index on customerId for faster queries
    await payments_collection.create_index([("customerId", 1)])
    
    # Create index on status for faster queries
    await payments_collection.create_index([("status", 1)])
    
    print(f"Connected to MongoDB: {settings.DATABASE_NAME}")
    print(f"Connected to Auth DB: {settings.AUTH_DATABASE_NAME}")
    print(f"Connected to Tuition DB: {settings.TUITION_DATABASE_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database():
    """Get payment database instance."""
    return database


def get_auth_database():
    """Get auth database instance for user operations."""
    return auth_database


def get_tuition_database():
    """Get tuition database instance for tuition operations."""
    return tuition_database
