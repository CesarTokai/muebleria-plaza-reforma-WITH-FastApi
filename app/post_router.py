from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schemas, crud_post, database, auth
from typing import List

router = APIRouter(prefix="/posts", tags=["posts"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden crear publicaciones
    return crud_post.create_post(db, post)

@router.get("/", response_model=List[schemas.PostOut])
def list_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_post.get_all_posts(db, skip, limit)

@router.get("/furniture/{furniture_id}", response_model=List[schemas.PostOut])
def get_posts_by_furniture(furniture_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_post.get_posts_by_furniture(db, furniture_id, skip, limit)

@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = crud_post.get_post(db, post_id)
    if not post or not post.is_active:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return post

@router.put("/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, post: schemas.PostUpdate, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden actualizar publicaciones
    return crud_post.update_post(db, post_id, post)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden eliminar publicaciones
    deleted = crud_post.delete_post(db, post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return None

@router.delete("/{post_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_post(post_id: int, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden eliminar permanentemente publicaciones
    deleted = crud_post.hard_delete_post(db, post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return None

@router.get("/inactive", response_model=List[schemas.PostOut])
def list_inactive_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden ver publicaciones inactivas
    return crud_post.get_inactive_posts(db, skip, limit)

@router.post("/{post_id}/restore", response_model=schemas.PostOut)
def restore_post(post_id: int, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    # Solo administradores pueden restaurar publicaciones
    return crud_post.restore_post(db, post_id)
