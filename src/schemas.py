from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr



class ContactBase(BaseModel):

    first_name : str
    last_name : str
    email : EmailStr
    phone : str
    birthday : date

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id : int

    class Config:
        from_attributes = True
