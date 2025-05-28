from sqlalchemy.orm import Session
from . import models, schemas, auth
from datetime import datetime, timedelta
import random

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.hashed_password):
        return False
    return user

def set_reset_code(db: Session, user: models.User):
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    user.reset_code = code
    user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    return code

def verify_reset_code(db: Session, email: str, code: str):
    user = get_user_by_email(db, email)
    if user and user.reset_code == code and user.reset_code_expiry > datetime.utcnow():
        return True
    return False

def reset_password(db: Session, email: str, code: str, new_password: str):
    user = get_user_by_email(db, email)
    if user and user.reset_code == code and user.reset_code_expiry > datetime.utcnow():
        user.hashed_password = auth.get_password_hash(new_password)
        user.reset_code = None
        user.reset_code_expiry = None
        db.commit()
        return True
    return False
