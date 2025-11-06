from __future__ import annotations

import base64
import hashlib
from decimal import Decimal
from typing import List, Optional, Dict

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from . import models, schemas
from .crud_category import get_category_by_id


# ====================== Helpers base ======================

def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e)).lower()
        if "foreign key" in msg or "cannot add or update a child row" in msg:
            raise HTTPException(status_code=400, detail="Violación de clave foránea") from e
        if "duplicate" in msg or "unique" in msg:
            raise HTTPException(status_code=409, detail="Registro duplicado") from e
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos") from e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de base de datos")

def _ensure_found(obj, name: str = "Recurso"):
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} no encontrado")
    return obj

def _split_data_url(s: str) -> tuple[Optional[str], str]:
    """
    Acepta base64 con o sin data URL.
    Regresa (mime|None, payload_base64).
    """
    s = (s or "").strip()
    if s.startswith("data:") and ";base64," in s:
        head, payload = s.split(";base64,", 1)
        mime = head.split("data:", 1)[1]
        return mime, payload
    return None, s

def _to_data_url(mime: str, data: bytes) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

def _sync_legacy_first_image(db: Session, furniture: models.Furniture) -> None:
    """Sincroniza furniture.img_base64 con la primera imagen por posición."""
    first = (
        db.query(models.FurnitureImage)
        .filter(models.FurnitureImage.furniture_id == furniture.id)
        .order_by(models.FurnitureImage.position.asc(), models.FurnitureImage.id.asc())
        .first()
    )
    furniture.img_base64 = _to_data_url(first.mime, first.bytes) if first else None


# ====================== CRUD Furniture ======================

def create_furniture(db: Session, furniture: schemas.FurnitureCreate) -> models.Furniture:
    # Validaciones mínimas
    if not getattr(furniture, "name", None) or not str(furniture.name).strip():
        raise HTTPException(status_code=422, detail="El campo 'name' es obligatorio y no puede estar vacío")
    if getattr(furniture, "price", None) is None:
        raise HTTPException(status_code=422, detail="El campo 'price' es obligatorio")
    try:
        if float(furniture.price) <= 0:
            raise HTTPException(status_code=422, detail="El campo 'price' debe ser mayor que 0")
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="El campo 'price' debe ser un número válido")
    if getattr(furniture, "category_id", None) is None:
        raise HTTPException(status_code=422, detail="El campo 'category_id' es obligatorio")

    # Categoría
    category = get_category_by_id(db, furniture.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Duplicado por (name, category_id)
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

    # Crear entidad base
    db_obj = models.Furniture(
        name=furniture.name.strip(),
        description=(furniture.description or "").strip() or None,
        price=Decimal(str(furniture.price)),
        category_id=furniture.category_id,
        category_name=(getattr(category, "name", "") or ""),   # usa la columna legado 'category' mapeada a category_name
        img_base64=None,  # se setea tras insertar imágenes
        stock=int(furniture.stock or 0),
        brand=(furniture.brand or "").strip() or None,
        color=(furniture.color or "").strip() or None,
        material=(furniture.material or "").strip() or None,
        dimensions=(furniture.dimensions or "").strip() or None,
    )
    db.add(db_obj)
    db.flush()  # necesitamos el id para las imágenes

    # Procesar imágenes (LONGBLOB)
    images_b64: List[str] = []
    if getattr(furniture, "images", None) is not None:
        if not isinstance(furniture.images, list):
            raise HTTPException(status_code=422, detail="El campo 'images' debe ser una lista de cadenas")
        images_b64 = [s.strip() for s in furniture.images if isinstance(s, str) and s.strip()]

    _insert_images_blob(db, db_obj, images_b64, start_position=0, dedupe=True)
    _sync_legacy_first_image(db, db_obj)

    _commit_or_rollback(db)
    db.refresh(db_obj)
    return db_obj


def get_furniture(db: Session, furniture_id: int) -> Optional[models.Furniture]:
    try:
        return (
            db.query(models.Furniture)
            .options(
                selectinload(models.Furniture.posts),
                selectinload(models.Furniture.category_rel) if hasattr(models.Furniture, "category_rel") else selectinload(models.Furniture.images),
                selectinload(models.Furniture.images),
            )
            .filter(models.Furniture.id == furniture_id)
            .first()
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al obtener mueble")


def get_all_furniture(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[str] = None,
        category_ids: Optional[List[int]] = None,
        order_by: str = "-created_at",
) -> List[models.Furniture]:
    try:
        q = db.query(models.Furniture).options(
            selectinload(models.Furniture.images),
        )
        # Filtrar por category_id (compatibilidad) o por category_ids (lista)
        if category_ids:
            # asegurarse que category_ids sea lista de ints
            q = q.filter(models.Furniture.category_id.in_(category_ids))
        elif category_id:
            q = q.filter(models.Furniture.category_id == category_id)

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
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al listar muebles")


def update_furniture(db: Session, furniture_id: int, furniture: schemas.FurnitureUpdate) -> models.Furniture:
    db_obj = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    data = furniture.dict(exclude_unset=True)

    # Si vienen imágenes, reemplazamos toda la colección
    if "images" in data:
        imgs = data.get("images")
        if imgs is None:
            # borrar todas
            db.query(models.FurnitureImage).filter(
                models.FurnitureImage.furniture_id == db_obj.id
            ).delete(synchronize_session=False)
            db_obj.img_base64 = None
        else:
            if not isinstance(imgs, list):
                raise HTTPException(status_code=422, detail="El campo 'images' debe ser una lista de cadenas")
            cleaned = [s.strip() for s in imgs if isinstance(s, str) and s.strip()]
            # reemplazo completo
            db.query(models.FurnitureImage).filter(
                models.FurnitureImage.furniture_id == db_obj.id
            ).delete(synchronize_session=False)
            db.flush()
            _insert_images_blob(db, db_obj, cleaned, start_position=0, dedupe=True)
            _sync_legacy_first_image(db, db_obj)

    # Si cambia la categoría, validar que exista y sincronizar texto legado
    if data.get("category_id") is not None:
        cat = get_category_by_id(db, data["category_id"])
        if not cat:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        db_obj.category_name = getattr(cat, "name", "") or ""

    # Duplicado por (name, category_id)
    new_name = data.get("name", db_obj.name)
    new_cat_id = data.get("category_id", db_obj.category_id)
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
            detail=f"Ya existe un mueble con nombre '{new_name}' en la categoría '{new_cat_id}'.",
        )

    # Aplicar resto de campos
    for k, v in data.items():
        if k == "images":
            continue
        if k == "price" and v is not None:
            try:
                v = Decimal(str(v))
            except Exception:
                raise HTTPException(status_code=400, detail="Precio inválido")
        if k == "category_id" and v is not None:
            # Si se actualiza la categoría, también actualizar el nombre
            cat = get_category_by_id(db, v)
            if not cat:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            db_obj.category_name = getattr(cat, "name", "") or ""
        if isinstance(v, str):
            v = v.strip() or None
        setattr(db_obj, k, v)

    _commit_or_rollback(db)
    db.refresh(db_obj)
    return db_obj


def delete_furniture(db: Session, furniture_id: int) -> bool:
    db_obj = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    try:
        db.delete(db_obj)
        _commit_or_rollback(db)
        return True
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al eliminar mueble")


def search_furniture(
        db: Session,
        term: Optional[str] = None,
        category_id: Optional[str] = None,
        category_ids: Optional[List[int]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "-created_at",
) -> List[models.Furniture]:
    try:
        q = db.query(models.Furniture).options(selectinload(models.Furniture.images))
        if term:
            like = f"%{term.strip()}%"
            q = q.filter(
                (models.Furniture.name.ilike(like)) |
                (models.Furniture.description.ilike(like))
            )
        # Filtrar por lista de categorías si se provee, si no usar category_id
        if category_ids:
            q = q.filter(models.Furniture.category_id.in_(category_ids))
        elif category_id:
            q = q.filter(models.Furniture.category_id == category_id)

        if min_price is not None:
            q = q.filter(models.Furniture.price >= float(min_price))

        if max_price is not None:
            q = q.filter(models.Furniture.price <= float(max_price))

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
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al buscar muebles")


def get_furniture_categories(db: Session) -> List[str]:
    try:
        rows = db.query(models.Category.name).order_by(models.Category.name.asc()).all()
        return [r[0] for r in rows if r and r[0]]
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al obtener categorías")


def create_furniture_batch(db: Session, furniture_list: List[schemas.FurnitureCreate]) -> List[models.Furniture]:
    created: List[models.Furniture] = []
    try:
        for furniture in furniture_list:
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

            db_obj = models.Furniture(
                name=furniture.name.strip(),
                description=(furniture.description or "").strip() or None,
                price=Decimal(str(furniture.price)),
                category_id=furniture.category_id,
                category_name=(getattr(category, "name", "") or ""),
                img_base64=None,
                stock=int(furniture.stock or 0),
                brand=(furniture.brand or "").strip() or None,
                color=(furniture.color or "").strip() or None,
                material=(furniture.material or "").strip() or None,
                dimensions=(furniture.dimensions or "").strip() or None,
            )
            db.add(db_obj)
            db.flush()

            images_b64 = []
            if getattr(furniture, "images", None) is not None:
                if not isinstance(furniture.images, list):
                    raise HTTPException(status_code=422, detail="El campo 'images' debe ser una lista de cadenas")
                images_b64 = [s.strip() for s in furniture.images if isinstance(s, str) and s.strip()]

            _insert_images_blob(db, db_obj, images_b64, start_position=0, dedupe=True)
            _sync_legacy_first_image(db, db_obj)

            created.append(db_obj)

        _commit_or_rollback(db)
        for o in created:
            db.refresh(o)
        return created

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear muebles en lote")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado al crear muebles en lote")


# ====================== CRUD de Imágenes (servicio) ======================

def _insert_images_blob(
        db: Session,
        furniture: models.Furniture,
        images_b64: List[str],
        start_position: int,
        dedupe: bool = True,
) -> List[models.FurnitureImage]:
    """
    Inserta imágenes LONGBLOB a partir de base64.
    - dedupe=True: evita duplicar por sha256 dentro del mismo mueble.
    """
    new_objs: List[models.FurnitureImage] = []
    existing_sha = set()
    if dedupe:
        existing_sha = {
            r[0]
            for r in db.query(models.FurnitureImage.sha256)
            .filter(models.FurnitureImage.furniture_id == furniture.id)
            .all()
        }

    for raw in images_b64:
        mime, payload = _split_data_url(raw)
        try:
            data = base64.b64decode(payload, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Imagen base64 inválida")

        sha = hashlib.sha256(data).digest()
        if dedupe and sha in existing_sha:
            continue
        existing_sha.add(sha)

        obj = models.FurnitureImage(
            furniture_id=furniture.id,
            position=start_position + len(new_objs),
            mime=mime or "application/octet-stream",
            bytes=data,
            size_bytes=len(data),
            sha256=sha,
        )
        db.add(obj)
        new_objs.append(obj)

    return new_objs


def add_images(db: Session, furniture_id: int, images_b64: List[str]) -> List[models.FurnitureImage]:
    mueble = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    if not isinstance(images_b64, list):
        raise HTTPException(status_code=422, detail="'images' debe ser una lista")
    images_b64 = [s.strip() for s in images_b64 if isinstance(s, str) and s.strip()]

    last_pos = (
        db.query(models.FurnitureImage.position)
        .filter(models.FurnitureImage.furniture_id == mueble.id)
        .order_by(models.FurnitureImage.position.desc())
        .first()
    )
    start = (last_pos[0] + 1) if last_pos else 0

    objs = _insert_images_blob(db, mueble, images_b64, start_position=start, dedupe=True)
    if mueble.img_base64 is None and objs:
        # setea legacy con la primera agregada en esta operación
        first = objs[0]
        mueble.img_base64 = _to_data_url(first.mime, first.bytes)

    _commit_or_rollback(db)
    for o in objs:
        db.refresh(o)
    return objs


def replace_images(db: Session, furniture_id: int, images_b64: List[str]) -> List[models.FurnitureImage]:
    mueble = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    if not isinstance(images_b64, list):
        raise HTTPException(status_code=422, detail="'images' debe ser una lista")
    images_b64 = [s.strip() for s in images_b64 if isinstance(s, str) and s.strip()]

    db.query(models.FurnitureImage).filter(
        models.FurnitureImage.furniture_id == mueble.id
    ).delete(synchronize_session=False)
    db.flush()

    objs = _insert_images_blob(db, mueble, images_b64, start_position=0, dedupe=True)
    _sync_legacy_first_image(db, mueble)

    _commit_or_rollback(db)
    for o in objs:
        db.refresh(o)
    return objs


def reorder_images(db: Session, furniture_id: int, order: Dict[int, int]) -> None:
    """
    Reordena usando técnica de posiciones negativas para evitar colisiones con UNIQUE(furniture_id, position).
    order: {image_id: new_position}
    """
    mueble = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    imgs = db.query(models.FurnitureImage).filter(
        models.FurnitureImage.furniture_id == mueble.id
    ).all()

    ids_in_db = {im.id for im in imgs}
    if not set(order.keys()).issubset(ids_in_db):
        raise HTTPException(status_code=400, detail="Una o más imágenes no pertenecen al mueble")

    # Paso 1: mover a posiciones negativas
    for im in imgs:
        if im.id in order:
            im.position = -(abs(im.position) + 1)
    db.flush()

    # Paso 2: aplicar nuevas posiciones explícitas
    for im in imgs:
        if im.id in order:
            im.position = int(order[im.id])

    # Paso 3: rellenar huecos para las no mencionadas
    used = set(order.values())
    rest = [im for im in imgs if im.id not in order]
    next_pos = 0
    while next_pos in used:
        next_pos += 1
    for im in sorted(rest, key=lambda x: (x.position, x.id)):
        while next_pos in used:
            next_pos += 1
        im.position = next_pos
        used.add(next_pos)

    _sync_legacy_first_image(db, mueble)
    _commit_or_rollback(db)


def delete_image(db: Session, furniture_id: int, image_id: int) -> None:
    mueble = _ensure_found(get_furniture(db, furniture_id), "Mueble")
    obj = db.query(models.FurnitureImage).filter_by(id=image_id, furniture_id=mueble.id).first()
    _ensure_found(obj, "Imagen")

    db.delete(obj)
    db.flush()

    # Renumerar 0..N-1
    imgs = (
        db.query(models.FurnitureImage)
        .filter(models.FurnitureImage.furniture_id == mueble.id)
        .order_by(models.FurnitureImage.position.asc(), models.FurnitureImage.id.asc())
        .all()
    )
    for idx, im in enumerate(imgs):
        im.position = idx

    _sync_legacy_first_image(db, mueble)
    _commit_or_rollback(db)
