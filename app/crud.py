from sqlalchemy.orm import Session
from . import models, schemas, auth
from datetime import datetime, timedelta
import random
from sqlalchemy.exc import SQLAlchemyError

def get_user_by_email(db: Session, email: str):
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    except SQLAlchemyError as e:
        print(f"Error al buscar usuario: {e}")
        return None

def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = auth.get_password_hash(user.password)
        db_user = models.User(email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al crear usuario: {e}")
        raise

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        print("Usuario no encontrado")
        return False
    if not auth.verify_password(password, user.hashed_password):
        print("Contraseña incorrecta")
        return False
    return user

def set_reset_code(db: Session, user: models.User):
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    user.reset_code = code
    user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
    try:
        db.commit()
        return code
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al guardar código de recuperación: {e}")
        raise

def verify_reset_code(db: Session, email: str, code: str):
    user = get_user_by_email(db, email)
    if not user:
        print("Usuario no encontrado para verificación de código")
        return False
    if user.reset_code != code:
        print("Código de recuperación incorrecto")
        return False
    if user.reset_code_expiry <= datetime.utcnow():
        print("Código de recuperación expirado")
        return False
    return True

def reset_password(db: Session, email: str, code: str, new_password: str):
    user = get_user_by_email(db, email)
    if not user:
        print("Usuario no encontrado para restablecer contraseña")
        return False
    if user.reset_code != code:
        print("Código de recuperación incorrecto para restablecer contraseña")
        return False
    if user.reset_code_expiry <= datetime.utcnow():
        print("Código de recuperación expirado para restablecer contraseña")
        return False
    try:
        user.hashed_password = auth.get_password_hash(new_password)
        user.reset_code = None
        user.reset_code_expiry = None
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al restablecer contraseña: {e}")
        return False
