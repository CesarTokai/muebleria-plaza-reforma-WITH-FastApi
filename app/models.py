from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Numeric, UniqueConstraint, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from .database import Base
import datetime
import base64

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
    # Usar MEDIUMTEXT para MySQL, Text como fallback para otros motores
    icon_base64 = Column(MEDIUMTEXT().with_variant(Text, "sqlite"), nullable=True)
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
    # Usar MEDIUMTEXT para MySQL (~16MB), Text como fallback para SQLite en tests
    img_base64 = Column(MEDIUMTEXT().with_variant(Text, "sqlite"), nullable=True)
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

    # nueva relación para múltiples imágenes
    images = relationship("FurnitureImage", back_populates="furniture", cascade="all, delete-orphan", order_by="(FurnitureImage.position, FurnitureImage.id)")

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


# Nuevo modelo para almacenar múltiples imágenes por mueble
class FurnitureImage(Base):
    __tablename__ = "furniture_images"
    id = Column(Integer, primary_key=True, index=True)
    furniture_id = Column(Integer, ForeignKey('furniture.id', ondelete='CASCADE'), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=0)
    mime = Column(String(100), nullable=False)
    # LONGBLOB en MySQL -> LargeBinary aquí
    bytes = Column(LargeBinary, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(LargeBinary(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    furniture = relationship("Furniture", back_populates="images")

    @property
    def img_base64(self) -> str:
        """Propiedad de conveniencia para retornar el contenido como data URL base64 (usada por Pydantic ORM)."""
        try:
            payload = base64.b64encode(self.bytes).decode("ascii")
            return f"data:{self.mime};base64,{payload}"
        except Exception:
            return ""
