from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from . import schemas, crud_furniture, crud_post, database, auth, crud_category
from typing import List, Optional

router = APIRouter(prefix="/furniture", tags=["furniture"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.FurnitureOut, status_code=status.HTTP_201_CREATED)
def create_furniture(furniture: schemas.FurnitureCreate, db: Session = Depends(get_db), 
                    current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    # Solo administradores pueden crear muebles
    return crud_furniture.create_furniture(db, furniture)

@router.post("/batch", response_model=List[schemas.FurnitureOut], status_code=status.HTTP_201_CREATED)
def create_furniture_batch(furniture_list: List[schemas.FurnitureCreate], db: Session = Depends(get_db), 
                          current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    # Solo administradores pueden crear muebles en lote
    # Usar operación transaccional para rollback completo si algo falla
    return crud_furniture.create_furniture_batch(db, furniture_list)

@router.get("/", response_model=List[schemas.FurnitureOut])
def list_furniture(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud_furniture.get_all_furniture(db, skip, limit, category_id)

@router.get("/search", response_model=List[schemas.FurnitureOut])
def search_furniture(
    term: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud_furniture.search_furniture(db, term, category_id, min_price, max_price, skip, limit)

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    # Devolver categorías desde la tabla `categories`
    return [c.name for c in crud_category.get_all_categories(db)]

@router.post("/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db),
                    current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    # Solo administradores pueden crear categorías
    return crud_category.create_category(db, category)

@router.get("/{furniture_id}", response_model=schemas.FurnitureOut)
def get_furniture(furniture_id: int, db: Session = Depends(get_db)):
    furniture = crud_furniture.get_furniture(db, furniture_id)
    if not furniture:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return furniture

@router.put("/{furniture_id}", response_model=schemas.FurnitureOut)
def update_furniture(
    furniture_id: int, 
    furniture: schemas.FurnitureUpdate, 
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    # Solo administradores pueden actualizar muebles
    updated = crud_furniture.update_furniture(db, furniture_id, furniture)
    if not updated:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return updated

@router.delete("/{furniture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_furniture(
    furniture_id: int, 
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    # Solo administradores pueden eliminar muebles
    deleted = crud_furniture.delete_furniture(db, furniture_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return None

# --- Publicaciones anidadas bajo muebles ---
@router.get("/{furniture_id}/posts", response_model=List[schemas.PostOut])
def list_posts_for_furniture(
    furniture_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud_post.get_posts_by_furniture(db, furniture_id, skip, limit)

@router.post("/{furniture_id}/posts", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post_for_furniture(
    furniture_id: int,
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    # Enforce path furniture_id over body furniture_id to avoid inconsistencias
    if post.furniture_id is not None and post.furniture_id != furniture_id:
        raise HTTPException(status_code=400, detail="El furniture_id del body no coincide con la ruta")
    post_data = schemas.PostCreate(title=post.title, content=post.content, furniture_id=furniture_id)
    return crud_post.create_post(db, post_data)
