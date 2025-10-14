from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from . import models, schemas
from .image_utils import validate_base64_image


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    try:
        existing = db.query(models.Category).filter(models.Category.name == category.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La categoría ya existe")

        icon = validate_base64_image(category.icon_base64)
        db_obj = models.Category(name=category.name.strip(), description=(category.description or "").strip() or None)
        # si el modelo tiene campo icon, asignarlo; si no, ignorar
        if hasattr(db_obj, 'icon_base64'):
            setattr(db_obj, 'icon_base64', icon)

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


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate) -> models.Category:
    try:
        db_obj = get_category_by_id(db, category_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

        data = category.dict(exclude_unset=True)

        # si se intenta cambiar el nombre, validar unicidad
        new_name = data.get('name') or db_obj.name
        if 'name' in data and data['name'] and data['name'].strip() != db_obj.name:
            existing = db.query(models.Category).filter(models.Category.name == data['name'].strip()).first()
            if existing and existing.id != db_obj.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe otra categoría con ese nombre")

        # validar icono si viene
        if 'icon_base64' in data:
            data['icon_base64'] = validate_base64_image(data.get('icon_base64'))

        # asignar campos
        for k, v in data.items():
            if isinstance(v, str):
                v = v.strip()
                v = v or None
            setattr(db_obj, k, v)

        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error al actualizar categoría") from e

        db.refresh(db_obj)
        return db_obj
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error inesperado al actualizar categoría") from e


def delete_category(db: Session, category_id: int) -> bool:
    try:
        db_obj = get_category_by_id(db, category_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

        # opcional: impedir borrado si hay muebles asociados
        associated = db.query(models.Furniture).filter(models.Furniture.category_id == db_obj.id).first()
        if associated:
            raise HTTPException(status_code=400, detail="No se puede eliminar categoría con muebles asociados")

        db.delete(db_obj)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error al eliminar categoría") from e
        return True
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error inesperado al eliminar categoría") from e
