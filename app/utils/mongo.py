import motor.motor_asyncio

from app.core.config import settings
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
try :
    db = client[settings.MONGO_DB_NAME]
    print("Connected to MongoDB")
except Exception as e:
    print("Error: ", e)