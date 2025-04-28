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
    username: Optional[str] = None

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    date: date

class TransactionCreate(TransactionBase):
    category_id: int

class TransactionResponse(TransactionBase):
    id: int
    owner_id: int
    category_id: int

    class Config:
        from_attributes = True
