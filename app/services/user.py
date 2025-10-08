from fastapi import HTTPException
from bson import ObjectId

from app.utils.mongo import db
from app.schemas.user import UserSignUp

class UserService:

    # Get user using user id
    async def get_user_by_id(self, user_id)-> dict:
        """
        Get user using user id
        """
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as e:
            raise
        
    # Get user by email for signup
    async def get_user_by_email_for_signup(self, user_email: str) -> dict:
        """
        Get user by email for signup
        """
        try:
            user = await db.users.find_one({"email" : user_email})
            return user
        
        except Exception as e:
            raise

    #Add user to database
    async def register_user(self, user_data: UserSignUp) -> str:
        """
        Add user to database
        """
        try:
            user_dict = user_data.dict()
            result = await db.users.insert_one(user_dict)
            inserted_id = str(result.inserted_id)
            return inserted_id
        except Exception as e:
            raise
        

    #Get user by email for login
    async def get_user_by_email(self, user_email:str)-> dict:
        """
        Get user by email for login
        """
        try:
            user = await db.users.find_one({"email": user_email})
            if user is None:
                raise HTTPException("User not found")
            return user
        except Exception as e:
            raise