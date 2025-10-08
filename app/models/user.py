from pydantic import BaseModel, Field

class CreateUser(BaseModel):
    email: str = Field(...)
    password: str = Field(...)
    name: str = Field(...)

class UserAuth(BaseModel):
    email: str = Field(...)
    password: str = Field(...)