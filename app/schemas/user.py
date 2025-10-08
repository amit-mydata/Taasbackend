from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class UserSignUp(BaseModel):
    name: str
    email: EmailStr
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)