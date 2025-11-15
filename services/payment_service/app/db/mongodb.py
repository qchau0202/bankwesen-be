from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# MongoDB client
client: AsyncIOMotorClient = None
database = None
auth_database = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, database, auth_database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    auth_database = client[settings.AUTH_DATABASE_NAME]
    
    # Create indexes for payment collection
    payments_collection = database["payments"]
    
    # Create partial unique index on tuitionId for pending/completed payments
    # This ensures only one active payment per tuition at the database level
    await payments_collection.create_index(
        [("tuitionId", 1)],
        name="unique_tuition_active_payment",
        unique=True,
        partialFilterExpression={"status": {"$in": ["pending", "completed"]}}
    )
    
    # Create index on customerId for faster queries
    await payments_collection.create_index([("customerId", 1)])
    
    # Create index on status for faster queries
    await payments_collection.create_index([("status", 1)])
    
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
    print(f"✅ Connected to Auth DB: {settings.AUTH_DATABASE_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("❌ Closed MongoDB connection")


def get_database():
    """Get payment database instance."""
    return database


def get_auth_database():
    """Get auth database instance for user operations."""
    return auth_database
