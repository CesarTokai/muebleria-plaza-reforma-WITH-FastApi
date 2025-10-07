from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from fastapi import HTTPException
import datetime
import logging

logger = logging.getLogger(__name__)

def create_post(db: Session, post: schemas.PostCreate):
    try:
        # Verificar que el mueble existe
        furniture = db.query(models.Furniture).filter(models.Furniture.id == post.furniture_id).first()
        if not furniture:
            raise HTTPException(status_code=404, detail="El mueble especificado no existe")

        # Crear la publicación
        db_post = models.Post(
            title=post.title,
            content=post.content,
            furniture_id=post.furniture_id,
            publication_date=datetime.datetime.utcnow()
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al crear publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al crear publicación")
    except Exception as e:
        logger.exception(f"Error inesperado al crear publicación: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado al crear publicación")

def get_post(db: Session, post_id: int) -> Optional[models.Post]:
    try:
        return db.query(models.Post).filter(models.Post.id == post_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener publicación")

def get_all_posts(db: Session, skip: int = 0, limit: int = 100) -> List[models.Post]:
    try:
        return db.query(models.Post).filter(models.Post.is_active == True).order_by(models.Post.publication_date.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al listar publicaciones: {e}")
        raise HTTPException(status_code=500, detail="Error al listar publicaciones")

def get_posts_by_furniture(db: Session, furniture_id: int, skip: int = 0, limit: int = 100) -> List[models.Post]:
    try:
        # Verificar que el mueble existe
        furniture = db.query(models.Furniture).filter(models.Furniture.id == furniture_id).first()
        if not furniture:
            raise HTTPException(status_code=404, detail="El mueble especificado no existe")

        return db.query(models.Post).filter(
            models.Post.furniture_id == furniture_id,
            models.Post.is_active == True
        ).order_by(models.Post.publication_date.desc()).offset(skip).limit(limit).all()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error al listar publicaciones del mueble: {e}")
        raise HTTPException(status_code=500, detail="Error al listar publicaciones del mueble")

def update_post(db: Session, post_id: int, post: schemas.PostUpdate):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # Actualizar solo los campos proporcionados
    data = post.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_post, key, value)

    try:
        db.commit()
        db.refresh(db_post)
        return db_post
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al actualizar publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar publicación")
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar publicación: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado al actualizar publicación")

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    try:
        # Soft delete - solo marcamos como inactivo
        db_post.is_active = False
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al eliminar publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar publicación")

def hard_delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    try:
        # Hard delete - eliminación física
        db.delete(db_post)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al eliminar permanentemente la publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar permanentemente la publicación")


def get_inactive_posts(db: Session, skip: int = 0, limit: int = 100) -> List[models.Post]:
    """Lista publicaciones marcadas como inactivas (papelera). Solo para administración."""
    try:
        return (
            db.query(models.Post)
            .filter(models.Post.is_active == False)
            .order_by(models.Post.publication_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Error al listar publicaciones inactivas: {e}")
        raise HTTPException(status_code=500, detail="Error al listar publicaciones inactivas")


def restore_post(db: Session, post_id: int) -> models.Post:
    """Restaura una publicación previamente eliminada (soft delete)."""
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    try:
        db_post.is_active = True
        db.commit()
        db.refresh(db_post)
        return db_post
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al restaurar publicación: {e}")
        raise HTTPException(status_code=500, detail="Error al restaurar publicación")
