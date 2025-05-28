from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
