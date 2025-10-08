import logging

from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from app.utils.auth import encrypt, decrypt, create_access_token
from app.models.user import CreateUser, UserAuth
from app.schemas.user import UserSignUp
from app.services.user import UserService

logger = logging.getLogger('fastapi')

user_router = APIRouter()   

# Register User
@user_router.post("/register")
async def register_user(request:Request, user: CreateUser):
    try:
        logger.info(f"Registering user with email: {user.email} - {request.method} - {request.url}")
        user_service = UserService()
        existing_user = await user_service.get_user_by_email_for_signup(user.email)

        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status" : False,
                    "message" : "User with this email already exists"
                }            
            )
        
        # Encrypt the user's password
        encrypted_password, encrypted_iv = encrypt(user.password)

        # Create UserSignup object with encrypted password and other user data
        user_data = UserSignUp(
            name = user.name,
            email = user.email,
            password = encrypted_password,
            iv = encrypted_iv
        )

        inserted_id = await user_service.register_user(user_data)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status" : True,
                "message" : "User registered successfully",
                "user_id" : inserted_id
            }
        )
    
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status" : False,
                "message" : "Internal Server Error"
            }
        )
    
# Login User
@user_router.post("/login")
async def login(request:Request, credentials: UserAuth):
    try:
        logger.info(f"Logging in user with email: {credentials.email} - {request.method} - {request.url}")
        email = credentials.email
        password = credentials.password
        user_sevice = UserService()

        try:
            user_dict = await user_sevice.get_user_by_email(email)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content = {
                    "status" : False,
                    "message" : "User does not exist with this email" 
                }
            )
        encrypted_password = user_dict.get("password")
        decrypted_password = decrypt(encrypted_password)
        
        try:
            if decrypted_password.decode('utf-8', 'ignore') != password:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content = {
                        "status" : False,
                        "message" : "Invalid email or password"
                    }
                )
            access_token = create_access_token(user_dict)
            return JSONResponse(
                status_code = status.HTTP_200_OK,
                content = {
                    "status" : True,
                    "data" : access_token,
                    "message" : "User login successful"
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code = status.HTTP_400_BAD_REQUEST,
                content = {
                    "status" : False,
                    "message" : "Invalid email or password"
                }
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error in login: {e}")
        return JSONResponse(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            content = {
                "status" : False,
                "message" : "Internal Server Error"
            }
        )