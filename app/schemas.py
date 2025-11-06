from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime


ALLOWED_CATEGORIES = {
    "sala","oficina","camas-y-colchones","comedor","cocinas",
    "electrodomesticos-pequenos","bicicletas","refrigeradores",
}




class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

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

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_base64: Optional[str] = None

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El nombre de la categoría no puede estar vacío')
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_base64: Optional[str] = None

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El nombre de la categoría no puede estar vacío')
        return v

class CategoryOut(CategoryBase):
    id: int
    created_at: Optional[datetime] = None

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

    @validator('new_password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class FurnitureBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    images: Optional[List[str]] = None  # nuevas múltiples imágenes (base64 or data URL)
    stock: Optional[int] = Field(0, ge=0)
    brand: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        if len(v) > 255:
            raise ValueError('El nombre no puede exceder 255 caracteres')
        return v

class FurnitureCreate(FurnitureBase):
    category_id: int

    @validator('category_id')
    def category_id_positive(cls, v):
        if v is None or v <= 0:
            raise ValueError('category_id debe ser un entero positivo')
        return v

class FurnitureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    images: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    brand: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('El nombre no puede estar vacío')
            if len(v) > 255:
                raise ValueError('El nombre no puede exceder 255 caracteres')
        return v

    @validator('category_id')
    def category_id_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('category_id debe ser un entero positivo')
        return v

class PostBase(BaseModel):
    title: str
    content: str
    furniture_id: int

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El título no puede estar vacío')
        if len(v) > 255:
            raise ValueError('El título no puede exceder 255 caracteres')
        return v

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El contenido no puede estar vacío')
        return v

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('title')
    def title_not_empty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('El título no puede estar vacío')
            if len(v) > 255:
                raise ValueError('El título no puede exceder 255 caracteres')
        return v

    @validator('content')
    def content_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El contenido no puede estar vacío')
        return v

class PostOut(PostBase):
    id: int
    publication_date: datetime
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# Nuevo esquema para representar imágenes asociadas al mueble
class FurnitureImageOut(BaseModel):
    id: int
    img_base64: str
    created_at: datetime

    class Config:
        orm_mode = True

class FurnitureOut(FurnitureBase):
    id: int
    created_at: datetime
    updated_at: datetime
    posts: List[PostOut] = Field(default_factory=list)
    category: Optional[str]  # Solo el nombre de la categoría
    images: List[FurnitureImageOut] = Field(default_factory=list)

    class Config:
        orm_mode = True
        fields = {"category": "category_name"}  # Mapea el campo category al atributo category_name del modelo
