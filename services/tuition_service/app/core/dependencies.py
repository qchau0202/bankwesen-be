from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_database
from app.core.security import get_current_user, get_current_student


def get_tuition_db(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Dependency to get tuition database."""
    return db


# Export commonly used dependencies
__all__ = [
    "get_tuition_db",
    "get_current_user",
    "get_current_student"
]
