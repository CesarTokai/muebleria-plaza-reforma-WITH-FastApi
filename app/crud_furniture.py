from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from fastapi import HTTPException
import base64

def create_furniture(db: Session, furniture: schemas.FurnitureCreate):
    try:
        # Validaciones por campo
        if not furniture.name or not furniture.name.strip():
            raise HTTPException(status_code=400, detail="El nombre del mueble es obligatorio")
        if len(furniture.name) > 100:
            raise HTTPException(status_code=400, detail="El nombre del mueble no debe exceder 100 caracteres")
        if not furniture.category or not furniture.category.strip():
            raise HTTPException(status_code=400, detail="La categoría es obligatoria")
        if furniture.price is None or furniture.price < 0:
            raise HTTPException(status_code=400, detail="El precio debe ser un número positivo")
        if furniture.stock is not None and furniture.stock < 0:
            raise HTTPException(status_code=400, detail="El stock no puede ser negativo")
        if furniture.img_base64:
            try:
                base64.b64decode(furniture.img_base64)
            except Exception:
                raise HTTPException(status_code=400, detail="Imagen en base64 inválida")
        if furniture.brand and len(furniture.brand) > 50:
            raise HTTPException(status_code=400, detail="La marca no debe exceder 50 caracteres")
        if furniture.color and len(furniture.color) > 30:
            raise HTTPException(status_code=400, detail="El color no debe exceder 30 caracteres")
        if furniture.material and len(furniture.material) > 50:
            raise HTTPException(status_code=400, detail="El material no debe exceder 50 caracteres")
        if furniture.dimensions and len(furniture.dimensions) > 100:
            raise HTTPException(status_code=400, detail="Las dimensiones no deben exceder 100 caracteres")
        db_furniture = models.Furniture(**furniture.dict())
        db.add(db_furniture)
        db.commit()
        db.refresh(db_furniture)
        return db_furniture
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al crear mueble: {e}")
        raise HTTPException(status_code=500, detail="Error al crear mueble")
    except Exception as e:
        print(f"Error inesperado al crear mueble: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado al crear mueble")

def get_furniture(db: Session, furniture_id: int) -> Optional[models.Furniture]:
    try:
        return db.query(models.Furniture).filter(models.Furniture.id == furniture_id).first()
    except SQLAlchemyError as e:
        print(f"Error al obtener mueble: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener mueble")

def get_all_furniture(db: Session, skip: int = 0, limit: int = 100) -> List[models.Furniture]:
    try:
        return db.query(models.Furniture).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"Error al listar muebles: {e}")
        raise HTTPException(status_code=500, detail="Error al listar muebles")

def update_furniture(db: Session, furniture_id: int, furniture: schemas.FurnitureUpdate):
    db_furniture = get_furniture(db, furniture_id)
    if not db_furniture:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    # Validaciones por campo solo si se actualizan
    data = furniture.dict(exclude_unset=True)
    if "name" in data:
        if not data["name"] or not data["name"].strip():
            raise HTTPException(status_code=400, detail="El nombre del mueble es obligatorio")
        if len(data["name"]) > 100:
            raise HTTPException(status_code=400, detail="El nombre del mueble no debe exceder 100 caracteres")
    if "category" in data:
        if not data["category"] or not data["category"].strip():
            raise HTTPException(status_code=400, detail="La categoría es obligatoria")
    if "price" in data:
        if data["price"] is None or data["price"] < 0:
            raise HTTPException(status_code=400, detail="El precio debe ser un número positivo")
    if "stock" in data:
        if data["stock"] is not None and data["stock"] < 0:
            raise HTTPException(status_code=400, detail="El stock no puede ser negativo")
    if "img_base64" in data and data["img_base64"]:
        try:
            base64.b64decode(data["img_base64"])
        except Exception:
            raise HTTPException(status_code=400, detail="Imagen en base64 inválida")
    if "brand" in data and data["brand"] and len(data["brand"]) > 50:
        raise HTTPException(status_code=400, detail="La marca no debe exceder 50 caracteres")
    if "color" in data and data["color"] and len(data["color"]) > 30:
        raise HTTPException(status_code=400, detail="El color no debe exceder 30 caracteres")
    if "material" in data and data["material"] and len(data["material"]) > 50:
        raise HTTPException(status_code=400, detail="El material no debe exceder 50 caracteres")
    if "dimensions" in data and data["dimensions"] and len(data["dimensions"]) > 100:
        raise HTTPException(status_code=400, detail="Las dimensiones no deben exceder 100 caracteres")
    for key, value in data.items():
        setattr(db_furniture, key, value)
    try:
        db.commit()
        db.refresh(db_furniture)
        return db_furniture
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al actualizar mueble: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar mueble")
    except Exception as e:
        print(f"Error inesperado al actualizar mueble: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado al actualizar mueble")

def delete_furniture(db: Session, furniture_id: int):
    db_furniture = get_furniture(db, furniture_id)
    if not db_furniture:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    try:
        db.delete(db_furniture)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error al eliminar mueble: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar mueble")
