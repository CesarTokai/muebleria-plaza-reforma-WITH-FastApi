from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    is_admin: bool

    class Config:
        orm_mode = True

class RequestReset(BaseModel):
    email: EmailStr

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class FurnitureBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    img_base64: Optional[str] = None
    stock: Optional[int] = 0
    brand: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None

class FurnitureCreate(FurnitureBase):
    pass

class FurnitureUpdate(FurnitureBase):
    pass

class FurnitureOut(FurnitureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
