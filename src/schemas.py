from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class ContactBase(BaseModel):

    first_name : str
    last_name : str
    email : EmailStr
    phone : str
    birthday : date
    additional_information: str

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id : int

    class Config:
        from_attributes = True

class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: str
    password: str = Field(min_length=6, max_length=10)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserDb(BaseModel):

    id: int
    username: str
    email: str
    created_at: datetime
    confirmed: bool
    avatar: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"

class RequestEmail(BaseModel):
    email: EmailStr

class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

class ResetPassword(BaseModel):
    password: str

    