from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    legal_form: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    legal_form: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_premium: bool
    is_admin: Optional[bool] = False  # Может быть None, по умолчанию False
    subscription_type: str
    subscription_expires: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
