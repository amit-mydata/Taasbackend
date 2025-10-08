import motor.motor_asyncio
from typing import Optional
from app.core.config import settings

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db = None

def get_db():
    """Lazily create an AsyncIOMotorClient after fork and return the DB handle."""
    global _client, _db
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
        _db = _client[settings.MONGO_DB_NAME]
        print("Connected to MongoDB")
    return _db