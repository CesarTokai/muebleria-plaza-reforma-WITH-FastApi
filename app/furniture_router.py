from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schemas, crud_furniture, database
from typing import List

router = APIRouter(prefix="/furniture", tags=["furniture"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=List[schemas.FurnitureOut], status_code=status.HTTP_201_CREATED)
def create_furniture(furniture_list: List[schemas.FurnitureCreate], db: Session = Depends(get_db)):
    created_furniture = []
    for furniture in furniture_list:
        created = crud_furniture.create_furniture(db, furniture)
        created_furniture.append(created)
    return created_furniture

@router.get("/", response_model=List[schemas.FurnitureOut])
def list_furniture(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_furniture.get_all_furniture(db, skip, limit)

@router.get("/{furniture_id}", response_model=schemas.FurnitureOut)
def get_furniture(furniture_id: int, db: Session = Depends(get_db)):
    furniture = crud_furniture.get_furniture(db, furniture_id)
    if not furniture:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return furniture

@router.put("/{furniture_id}", response_model=schemas.FurnitureOut)
def update_furniture(furniture_id: int, furniture: schemas.FurnitureUpdate, db: Session = Depends(get_db)):
    updated = crud_furniture.update_furniture(db, furniture_id, furniture)
    if not updated:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return updated

@router.delete("/{furniture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_furniture(furniture_id: int, db: Session = Depends(get_db)):
    deleted = crud_furniture.delete_furniture(db, furniture_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return None
