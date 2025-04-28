from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    date: date
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str]
    date: date
    owner_id: int

    class Config:
        from_attributes = True