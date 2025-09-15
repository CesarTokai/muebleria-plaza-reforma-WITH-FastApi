from sqlalchemy.orm import Session
from . import models, schemas, auth
from datetime import datetime, timedelta
import random
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import re
import logging

logger = logging.getLogger(__name__)

def get_user_by_email(db: Session, email: str):
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    except SQLAlchemyError as e:
        logger.error(f"Error al buscar usuario: {e}")
        raise HTTPException(status_code=500, detail="Error al buscar usuario")

def create_user(db: Session, user: schemas.UserCreate):
    try:
        # Verificar si ya existe un usuario con ese email
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

        # Validar contraseña
        if len(user.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        # Validar complejidad de la contraseña (opcional)
        if not re.search(r'[A-Z]', user.password):
            raise HTTPException(status_code=400, detail="La contraseña debe contener al menos una letra mayúscula")

        if not re.search(r'[0-9]', user.password):
            raise HTTPException(status_code=400, detail="La contraseña debe contener al menos un número")

        hashed_password = auth.get_password_hash(user.password)
        db_user = models.User(email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al crear usuario: {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario")

def authenticate_user(db: Session, email: str, password: str):
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False
        if not auth.verify_password(password, user.hashed_password):
            return False
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Usuario inactivo")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al autenticar usuario: {e}")
        raise HTTPException(status_code=500, detail="Error al autenticar usuario")

def set_reset_code(db: Session, user: models.User):
    try:
        # Generar código aleatorio de 6 dígitos
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        user.reset_code = code
        user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
        db.commit()
        return code
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al guardar código de recuperación: {e}")
        raise HTTPException(status_code=500, detail="Error al generar código de recuperación")

def verify_reset_code(db: Session, email: str, code: str):
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False
        if user.reset_code != code:
            return False
        if user.reset_code_expiry <= datetime.utcnow():
            return False
        return True
    except Exception as e:
        logger.exception(f"Error al verificar código: {e}")
        raise HTTPException(status_code=500, detail="Error al verificar código")

def reset_password(db: Session, email: str, code: str, new_password: str):
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False
        if user.reset_code != code:
            return False
        if user.reset_code_expiry <= datetime.utcnow():
            return False

        # Validar contraseña
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        # Validar complejidad de la contraseña (opcional)
        if not re.search(r'[A-Z]', new_password):
            raise HTTPException(status_code=400, detail="La contraseña debe contener al menos una letra mayúscula")

        if not re.search(r'[0-9]', new_password):
            raise HTTPException(status_code=400, detail="La contraseña debe contener al menos un número")

        user.hashed_password = auth.get_password_hash(new_password)
        user.reset_code = None
        user.reset_code_expiry = None
        db.commit()
        return True
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al restablecer contraseña: {e}")
        raise HTTPException(status_code=500, detail="Error al restablecer contraseña")

def create_admin_user(db: Session, user: schemas.UserCreate):
    """Función para crear un usuario administrador"""
    try:
        # Verificar si ya existe un usuario con ese email
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

        # Validar contraseña
        if len(user.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        hashed_password = auth.get_password_hash(user.password)
        db_user = models.User(
            email=user.email, 
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al crear usuario administrador: {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario administrador")
