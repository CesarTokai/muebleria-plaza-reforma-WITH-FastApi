from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    reset_code = Column(String(6), nullable=True)  # Para el código de recuperación
    reset_code_expiry = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)  # Nuevo campo para roles

class Furniture(Base):
    __tablename__ = "furniture"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    img_base64 = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    brand = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    material = Column(String(100), nullable=True)
    dimensions = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
