import base64

from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi import HTTPException, status, Depends
from Crypto.Util.Padding import pad,unpad
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from typing import Optional
from jose import jwt

from app.core.config import settings
from app.services.user import UserService 

expires_delta = settings.ACCESS_TOKEN_EXPIRE_TIME

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="auth", tokenUrl="token")

# Encrypt the password using AES Key and IV Key
def encrypt(data):
    try:
        key = settings.AES_KEY
        iv = settings.IV_KEY    
        data = pad(data.encode("utf-8"), 16)
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted_data = base64.b64encode(cipher.encrypt(data)).decode("utf-8")
        return encrypted_data, base64.b64encode(cipher.iv).decode("utf-8")

    except Exception as e:
        raise

# Decrypt the password using AES Key and IV Key
def decrypt(enc):
    try:
        key = settings.AES_KEY
        iv = settings.IV_KEY

        enc = base64.b64decode(enc)
        if key is None:
            raise ValueError("Invalid key: key is None")

        key = key.encode("utf-8")
        if len(key) not in [16, 24, 32]:
            raise ValueError("Invalid key length: must be 16, 24, or 32 bytes")

        if iv is None:
            raise ValueError("Invalid IV: IV is None")

        iv = iv.encode("utf-8")
        if len(iv) != 16:
            raise ValueError("Invalid IV length: must be 16 bytes")

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(enc), 16)
        return decrypted_data
    except Exception as e:
        raise


# create access token
def create_access_token(user_dict: dict, expires_delta: Optional[timedelta] = None):
    to_encode = {"id": str(user_dict["_id"])}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=int(settings.ACCESS_TOKEN_EXPIRE_TIME))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

# get current user using token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("id")
        user_service = UserService()
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = await user_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )