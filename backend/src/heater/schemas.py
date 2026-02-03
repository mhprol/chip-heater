from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InstanceCreate(BaseModel):
    name: str

class InstanceResponse(BaseModel):
    id: int
    name: str
    status: str
    warming_enabled: bool
    messages_today: int

    class Config:
        from_attributes = True
