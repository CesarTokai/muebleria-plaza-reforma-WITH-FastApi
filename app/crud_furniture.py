from __future__ import annotations

import base64
import binascii
from typing import List, Optional, Tuple
from decimal import Decimal

from fastapi import HTTPException, status
import logging
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from . import models, schemas
from .crud_category import get_category_by_id


# ---------- Utilidades internas ----------

_MAX_IMG_BYTES = 2 * 1024 * 1024  # 2 MB (ajusta si necesitas más)
_ALLOWED_IMG_MIME_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,")

def _strip_data_url_prefix(b64: str) -> Tuple[str, Optional[str]]:
    """
    Si viene como data URL (data:image/png;base64,AAAA...), separa el prefijo y regresa (payload_base64, mime).
    Si no hay prefijo, regresa (b64, None).
    """
    for p in _ALLOWED_IMG_MIME_PREFIXES:
        if b64.startswith(p):
            return b64[len(p):], p.split(";")[0].split(":")[1]
    return b64, None

def _validate_base64_image(b64: Optional[str]) -> Optional[str]:
    """
    - Permite string vacío o None (sin imagen).
    - Acepta data URL o base64 “puro”.
    - Valida que decodifique y no exceda _MAX_IMG_BYTES.
    - No altera el formato salvo remover espacios/blancos accidentales.
    Retorna el MISMO formato de entrada (si venía con data URL, lo conserva).
    """
    if not b64:
        return None

    original = b64.strip()

    # separa y valida
    payload, _mime = _strip_data_url_prefix(original)
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Imagen en base64 inválida")

    if len(raw) > _MAX_IMG_BYTES:
        raise HTTPException(status_code=413, detail=f"La imagen excede {_MAX_IMG_BYTES // (1024*1024)}MB")

    # si todo OK, regresa el original (respetando si incluía el prefijo data URL)
    return original

def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logging.getLogger(__name__).exception("Integrity error on DB commit")
        # Determinar si es violación FK o unique
        msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'foreign key' in msg.lower() or 'cannot add or update a child row' in msg.lower():
            raise HTTPException(status_code=400, detail="Violación de clave foránea o categoría inexistente") from e
        if 'duplicate' in msg.lower() or 'unique' in msg.lower():
            raise HTTPException(status_code=409, detail="Registro duplicado en la base de datos") from e
        # fallback
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos") from e
    except SQLAlchemyError as e:
        db.rollback()
        logging.getLogger(__name__).exception("Database error on commit")
        # Inspeccionar mensaje para errores comunes de esquema y devolver detalle útil
        msg = ''
        try:
            msg = str(e.orig)
        except Exception:
            msg = str(e)
        ml = msg.lower()
        if 'unknown column' in ml or '1054' in ml or 'column not found' in ml or 'no such column' in ml:
            # Mensaje orientativo, no exponer SQL completo
            raise HTTPException(status_code=500, detail="Error de esquema en la base de datos: columna faltante o desalineada. Revisar migraciones y el esquema de la tabla.") from e
        # Fallback genérico
        raise HTTPException(status_code=500, detail="Error de base de datos") from e

def _ensure_found(obj, name: str = "Recurso"):
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} no encontrado")
    return obj


# ---------- Operaciones CRUD ----------

def create_furniture(db: Session, furniture: schemas.FurnitureCreate) -> models.Furniture:
    """
    Crea un mueble con validación de imagen, campos y duplicados razonables.
    """
    # Validaciones tempranas para dar retroalimentación clara (422) si falta algo
    if not getattr(furniture, 'name', None) or not str(furniture.name).strip():
        raise HTTPException(status_code=422, detail="El campo 'name' es obligatorio y no puede estar vacío")
    if getattr(furniture, 'price', None) is None:
        raise HTTPException(status_code=422, detail="El campo 'price' es obligatorio")
    try:
        if float(furniture.price) <= 0:
            raise HTTPException(status_code=422, detail="El campo 'price' debe ser mayor que 0")
    except ValueError:
        raise HTTPException(status_code=422, detail="El campo 'price' debe ser un número válido")
    if getattr(furniture, 'category_id', None) is None:
        raise HTTPException(status_code=422, detail="El campo 'category_id' es obligatorio")

    # Validar que la categoría exista
    category = get_category_by_id(db, furniture.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Evitar duplicados por nombre+category_id
    exists = (
        db.query(models.Furniture)
        .filter(models.Furniture.name == furniture.name)
        .filter(models.Furniture.category_id == furniture.category_id)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un mueble con nombre '{furniture.name}' en la categoría '{category.name}'."
        )

    img_b64 = _validate_base64_image(furniture.img_base64)

    db_obj = models.Furniture(
        name=furniture.name.strip(),
        description=(furniture.description or "").strip() or None,
        # Convertir y validar precio
        price=(lambda v: (lambda x: x)(Decimal(str(v))) if v is not None else None)(furniture.price),
        category_id=furniture.category_id,
        # Mantener compatibilidad con columna física antigua 'category' — nunca enviar NULL
        category_name=(category.name if (category and getattr(category, 'name', None)) else ''),
        img_base64=img_b64,
        stock=int(furniture.stock or 0),
        brand=(furniture.brand or "").strip() or None,
        color=(furniture.color or "").strip() or None,
        material=(furniture.material or "").strip() or None,
        dimensions=(furniture.dimensions or "").strip() or None,
    )

    db.add(db_obj)
    _commit_or_rollback(db)
    db.refresh(db_obj)
    return db_obj


def get_furniture(db: Session, furniture_id: int) -> Optional[models.Furniture]:
    """
    Obtiene un mueble por id (o None).
    """
    try:
        return db.query(models.Furniture).options(selectinload(models.Furniture.posts), selectinload(models.Furniture.category)).filter(models.Furniture.id == furniture_id).first()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al obtener mueble") from e


def get_all_furniture(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[str] = None,
        order_by: str = "-created_at",  # "-campo" = desc, "campo" = asc
) -> List[models.Furniture]:
    """
    Lista muebles con filtro opcional por categoría y orden configurable.
    """
    try:
        q = db.query(models.Furniture).options(selectinload(models.Furniture.posts), selectinload(models.Furniture.category))
        if category_id:
            q = q.filter(models.Furniture.category_id == category_id)

        # ordenamiento sencillo
        mapping = {
            "created_at": models.Furniture.created_at,
            "price": models.Furniture.price,
            "name": models.Furniture.name,
            "stock": models.Furniture.stock,
        }
        descending = order_by.startswith("-")
        key = order_by[1:] if descending else order_by
        col = mapping.get(key, models.Furniture.created_at)
        q = q.order_by(col.desc() if descending else col.asc())

        # límites razonables
        limit = max(1, min(500, int(limit)))
        skip = max(0, int(skip))

        return q.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al listar muebles") from e


def update_furniture(db: Session, furniture_id: int, furniture: schemas.FurnitureUpdate) -> models.Furniture:
    """
    Actualiza parcialmente un mueble (solo campos provistos).
    """
    db_obj = _ensure_found(get_furniture(db, furniture_id), "Mueble")

    # Edit: reemplazo de .model_dump por .dict para compatibilidad con Pydantic v1
    # Use `.dict(exclude_unset=True)` which es compatible con Pydantic v1 (y evita errores
    # si la instalación local no usa pydantic v2). Si tu proyecto usa pydantic v2 de forma
    # intencional, cambia esto a `model_dump` y fija la dependencia en requirements.
    data = furniture.dict(exclude_unset=True)

    if "img_base64" in data:
        data["img_base64"] = _validate_base64_image(data["img_base64"])

    new_name = data.get("name", db_obj.name)
    new_cat_id = data.get("category_id", db_obj.category_id)

    # Si se cambia category_id, validar que exista
    if data.get("category_id") is not None:
        cat = get_category_by_id(db, data["category_id"])
        if not cat:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    duplicate = (
        db.query(models.Furniture)
        .filter(models.Furniture.id != db_obj.id)
        .filter(models.Furniture.name == new_name)
        .filter(models.Furniture.category_id == new_cat_id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un mueble con nombre '{new_name}' en la categoría '{new_cat_id}'."
        )

    # aplica cambios
    for k, v in data.items():
        if k == "price" and v is not None:
            # Convertir a Decimal para Numeric DB
            try:
                v = Decimal(str(v))
            except Exception:
                raise HTTPException(status_code=400, detail="Precio inválido")
        if isinstance(v, str):
            v = v.strip()
            v = v or None  # normaliza strings vacíos a None
        setattr(db_obj, k, v)

    _commit_or_rollback(db)
    db.refresh(db_obj)
    return db_obj


def delete_furniture(db: Session, furniture_id: int) -> bool:
    """
    Elimina un mueble. Si hay publicaciones asociadas, se eliminan por la cascada
    (ya la definiste en el modelo), o cambia esta lógica si prefieres impedirlo.
    """
    db_obj = _ensure_found(get_furniture(db, furniture_id), "Mueble")

    try:
        db.delete(db_obj)
        _commit_or_rollback(db)
        return True
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al eliminar mueble") from e


def search_furniture(
        db: Session,
        term: Optional[str] = None,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "-created_at",
) -> List[models.Furniture]:
    """
    Búsqueda flexible por término (nombre/descr), categoría y rango de precio.
    """
    try:
        q = db.query(models.Furniture).options(selectinload(models.Furniture.posts), selectinload(models.Furniture.category))

        if term:
            like = f"%{term.strip()}%"
            q = q.filter(
                (models.Furniture.name.ilike(like)) |
                (models.Furniture.description.ilike(like))
            )

        if category_id:
            q = q.filter(models.Furniture.category_id == category_id)

        if min_price is not None:
            q = q.filter(models.Furniture.price >= float(min_price))

        if max_price is not None:
            q = q.filter(models.Furniture.price <= float(max_price))

        # orden idéntico al de get_all_furniture
        mapping = {
            "created_at": models.Furniture.created_at,
            "price": models.Furniture.price,
            "name": models.Furniture.name,
            "stock": models.Furniture.stock,
        }
        descending = order_by.startswith("-")
        key = order_by[1:] if descending else order_by
        col = mapping.get(key, models.Furniture.created_at)
        q = q.order_by(col.desc() if descending else col.asc())

        limit = max(1, min(500, int(limit)))
        skip = max(0, int(skip))
        return q.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al buscar muebles") from e


def get_furniture_categories(db: Session) -> List[str]:
    """
    Regresa la lista de categorías distintas presentes en la BD.
    """
    try:
        rows = db.query(models.Category.name).order_by(models.Category.name.asc()).all()
        return [r[0] for r in rows if r and r[0]]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al obtener categorías") from e


def create_furniture_batch(db: Session, furniture_list: List[schemas.FurnitureCreate]) -> List[models.Furniture]:
    """Crea varios muebles en una sola transacción. Si alguno falla, se revierte todo."""
    created: List[models.Furniture] = []
    try:
        # Validaciones y creación en memoria (evita commits parciales)
        for furniture in furniture_list:
            # validar categoria
            category = get_category_by_id(db, furniture.category_id)
            if not category:
                raise HTTPException(status_code=404, detail=f"Categoría no encontrada para '{furniture.name}'")

            exists = (
                db.query(models.Furniture)
                .filter(models.Furniture.name == furniture.name)
                .filter(models.Furniture.category_id == furniture.category_id)
                .first()
            )
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un mueble con nombre '{furniture.name}' en la categoría '{category.name}'."
                )

            img_b64 = _validate_base64_image(furniture.img_base64)

            db_obj = models.Furniture(
                name=furniture.name.strip(),
                description=(furniture.description or "").strip() or None,
                price=Decimal(str(furniture.price)),
                category_id=furniture.category_id,
                # Mantener compatibilidad con columna física antigua 'category'
                category_name=(category.name if (category and getattr(category, 'name', None)) else ''),
                img_base64=img_b64,
                stock=int(furniture.stock or 0),
                brand=(furniture.brand or "").strip() or None,
                color=(furniture.color or "").strip() or None,
                material=(furniture.material or "").strip() or None,
                dimensions=(furniture.dimensions or "").strip() or None,
            )
            db.add(db_obj)
            created.append(db_obj)

        # Commit único
        _commit_or_rollback(db)
        for o in created:
            db.refresh(o)
        return created
    except HTTPException:
        # preserve original HTTP exceptions
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear muebles en lote") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado al crear muebles en lote") from e
