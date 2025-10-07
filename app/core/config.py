from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List, Union
from pydantic import validator
import os

load_dotenv()

class Settings(BaseSettings):
   
    GEMINI_API_KEY : str = os.environ.get("GEMINI_API_KEY")
    MONGO_URI: str = os.environ.get("MONGO_URI")
    MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME")
    REDIS_URL: str = os.environ.get("REDIS_URL")
    BACKEND_CORS_ORIGINS: List = []

    @validator("BACKEND_CORS_ORIGINS", pre=True, allow_reuse=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    STATIC_FILE :str= "static"

settings = Settings()
