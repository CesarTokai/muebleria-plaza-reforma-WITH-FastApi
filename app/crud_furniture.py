from __future__ import annotations

import base64
import binascii
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from . import models, schemas


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
    except SQLAlchemyError as e:
        db.rollback()
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
    # (Opcional) evita duplicados obvios por nombre+categoría
    exists = (
        db.query(models.Furniture)
        .filter(models.Furniture.name == furniture.name, models.Furniture.category == furniture.category)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un mueble con nombre '{furniture.name}' en la categoría '{furniture.category}'."
        )

    img_b64 = _validate_base64_image(furniture.img_base64)

    db_obj = models.Furniture(
        name=furniture.name.strip(),
        description=(furniture.description or "").strip() or None,
        price=float(furniture.price),
        category=furniture.category,
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
        return db.query(models.Furniture).filter(models.Furniture.id == furniture_id).first()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al obtener mueble") from e


def get_all_furniture(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        order_by: str = "-created_at",  # "-campo" = desc, "campo" = asc
) -> List[models.Furniture]:
    """
    Lista muebles con filtro opcional por categoría y orden configurable.
    """
    try:
        q = db.query(models.Furniture)
        if category:
            q = q.filter(models.Furniture.category == category)

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

    data = furniture.model_dump(exclude_unset=True)

    if "img_base64" in data:
        data["img_base64"] = _validate_base64_image(data["img_base64"])

    # (Opcional) evita duplicado nombre+categoría al cambiar esos campos
    new_name = data.get("name", db_obj.name)
    new_cat = data.get("category", db_obj.category)
    duplicate = (
        db.query(models.Furniture)
        .filter(
            models.Furniture.id != db_obj.id,
            models.Furniture.name == new_name,
            models.Furniture.category == new_cat,
            )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un mueble con nombre '{new_name}' en la categoría '{new_cat}'."
        )

    # aplica cambios
    for k, v in data.items():
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
        category: Optional[str] = None,
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
        q = db.query(models.Furniture)

        if term:
            like = f"%{term.strip()}%"
            q = q.filter(
                (models.Furniture.name.ilike(like)) |
                (models.Furniture.description.ilike(like))
            )

        if category:
            q = q.filter(models.Furniture.category == category)

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
        rows = db.query(models.Furniture.category).distinct().all()
        return [r[0] for r in rows if r and r[0]]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error al obtener categorías") from e
