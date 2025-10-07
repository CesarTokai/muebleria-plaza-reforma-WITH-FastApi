from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from . import models, schemas


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    try:
        existing = db.query(models.Category).filter(models.Category.name == category.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La categoría ya existe")
        db_obj = models.Category(name=category.name.strip(), description=(category.description or "").strip() or None)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear categoría") from e


def get_category_by_id(db: Session, category_id: int) -> Optional[models.Category]:
    try:
        return db.query(models.Category).filter(models.Category.id == category_id).first()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al obtener categoría")


def get_all_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.Category]:
    try:
        limit = max(1, min(500, int(limit)))
        skip = max(0, int(skip))
        return db.query(models.Category).order_by(models.Category.name.asc()).offset(skip).limit(limit).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al listar categorías")

