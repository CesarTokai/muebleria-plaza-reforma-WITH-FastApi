from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    reset_code = Column(String(6), nullable=True)
    reset_code_expiry = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    icon_base64 = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # relación inversa
    furniture = relationship("Furniture", back_populates="category")


class Furniture(Base):
    __tablename__ = "furniture"
    __table_args__ = (UniqueConstraint('name', 'category_id', name='uix_name_category'),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, index=True)
    # Mapeo para compatibilidad: columna física 'category' (varchar) existente en la BD
    category_name = Column('category', String(100), nullable=True)
    img_base64 = Column(Text, nullable=True)
    stock = Column(Integer, default=0)
    brand = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    material = Column(String(100), nullable=True)
    dimensions = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # relación con categoría (objeto)
    category = relationship("Category", back_populates="furniture")
    posts = relationship("Post", back_populates="furniture", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    publication_date = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    furniture_id = Column(Integer, ForeignKey("furniture.id"), nullable=False)

    # relación inversa
    furniture = relationship("Furniture", back_populates="posts")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    is_active = Column(Boolean, default=True)