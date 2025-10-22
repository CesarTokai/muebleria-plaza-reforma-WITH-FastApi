from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from . import schemas, crud_furniture, crud_post, database, auth, crud_category
from typing import List, Optional, Dict
import logging

router = APIRouter(prefix="/furniture", tags=["furniture"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.FurnitureOut, status_code=status.HTTP_201_CREATED)
async def create_furniture(request: Request, db: Session = Depends(get_db),
                    current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    # Leer y loguear body crudo para depuración
    logger = logging.getLogger(__name__)
    try:
        body = await request.json()
        logger.info(f"create_furniture RAW BODY: {body}")
    except Exception:
        logger.exception("No se pudo leer body crudo")
        body = None

    if body is None:
        raise HTTPException(status_code=400, detail="Body inválido o no JSON")

    # Compatibilidad: si el cliente envía 'img_base64' legacy, mapear a 'images' (lista)
    if isinstance(body, dict) and 'images' not in body and 'img_base64' in body and body.get('img_base64'):
        img_val = body.get('img_base64')
        if isinstance(img_val, str) and img_val.strip():
            body['images'] = [img_val]
            body.pop('img_base64', None)
            logger.info("Mapped legacy 'img_base64' to 'images' list for compatibility")

    # Log body mapeado antes de la validación Pydantic
    logger.info(f"create_furniture MAPPED BODY: {body}")

    # Parsear con Pydantic
    try:
        furniture = schemas.FurnitureCreate(**body)
    except Exception as e:
        logger.exception(f"Error al parsear FurnitureCreate: {e}")
        raise HTTPException(status_code=422, detail=f"Error de validación: {e}")

    # Log del objeto Pydantic antes de crear
    try:
        logger.info(f"create_furniture PARSED furniture.images: {getattr(furniture, 'images', None)}")
        logger.info(f"create_furniture PARSED furniture.dict(): {furniture.dict()}")
    except Exception:
        logger.exception("Error al loguear furniture parsed")

    return crud_furniture.create_furniture(db, furniture)

@router.post("/batch", response_model=List[schemas.FurnitureOut], status_code=status.HTTP_201_CREATED)
async def create_furniture_batch(request: Request, db: Session = Depends(get_db),
                          current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    logger = logging.getLogger(__name__)
    try:
        body = await request.json()
        logger.info(f"create_furniture_batch RAW BODY: {body}")
    except Exception:
        logger.exception("No se pudo leer body crudo en batch")
        body = None

    if body is None or not isinstance(body, list):
        raise HTTPException(status_code=400, detail="Body inválido: se espera una lista de muebles")

    # Compatibilidad batch: mapear img_base64 -> images en cada item si aplica
    for idx, item in enumerate(body):
        if isinstance(item, dict) and 'images' not in item and 'img_base64' in item and item.get('img_base64'):
            img_val = item.get('img_base64')
            if isinstance(img_val, str) and img_val.strip():
                item['images'] = [img_val]
                item.pop('img_base64', None)
                logger.info(f"Mapped legacy 'img_base64' to 'images' for batch item idx={idx}")

    # Log mapped batch body
    logger.info(f"create_furniture_batch MAPPED BODY: {body}")

    try:
        furniture_list = [schemas.FurnitureCreate(**item) for item in body]
    except Exception as e:
        logger.exception(f"Error al parsear batch FurnitureCreate: {e}")
        raise HTTPException(status_code=422, detail=f"Error de validación en batch: {e}")

    # Log parsed images for each item
    for i, f in enumerate(furniture_list):
        logger.info(f"create_furniture_batch PARSED item {i} images: {getattr(f, 'images', None)}")

    return crud_furniture.create_furniture_batch(db, furniture_list)

@router.get("/", response_model=List[schemas.FurnitureOut])
def list_furniture(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    category_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Listado de muebles. Puede filtrar por `category_id` (único) o `category_ids` (múltiples).
    Ejemplos:
      /furniture/?category_id=1
      /furniture/?category_ids=1&category_ids=2
    """
    # Si se provee category_ids, pasarlo al CRUD; si no, pasar category_id como antes
    return crud_furniture.get_all_furniture(db, skip, limit, category_id, category_ids)

@router.get("/search", response_model=List[schemas.FurnitureOut])
def search_furniture(
    term: Optional[str] = None,
    category_id: Optional[int] = None,
    category_ids: Optional[List[int]] = Query(None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Búsqueda flexible con término, categorías (single o multiple) y rango de precio."""
    return crud_furniture.search_furniture(db, term, category_id, category_ids, min_price, max_price, skip, limit)

@router.get("/categories", response_model=List[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    # Devolver categorías completas desde la tabla `categories`
    return crud_category.get_all_categories(db)

@router.post("/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db),
                    current_user: schemas.UserOut = Depends(auth.get_admin_user)):
    # Solo administradores pueden crear categorías
    return crud_category.create_category(db, category)

@router.get("/categories/{category_id}", response_model=schemas.CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud_category.get_category_by_id(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat

@router.put("/categories/{category_id}", response_model=schemas.CategoryOut)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    updated = crud_category.update_category(db, category_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return updated

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    deleted = crud_category.delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return None

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
    """Elimina un mueble por id (requiere administrador)."""
    deleted = crud_furniture.delete_furniture(db, furniture_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return None

@router.delete("/{furniture_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_furniture_trailing(
    furniture_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    """Alias con slash final para borrar un mueble (compatibilidad con clientes que agregan trailing slash)."""
    deleted = crud_furniture.delete_furniture(db, furniture_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mueble no encontrado")
    return None

# Endpoints nuevos para images
@router.post("/{furniture_id}/images", response_model=List[schemas.FurnitureImageOut], status_code=status.HTTP_201_CREATED)
def add_images(
    furniture_id: int,
    images: List[str],
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    """Agrega imágenes (lista base64/data URLs) al mueble."""
    objs = crud_furniture.add_images(db, furniture_id, images)
    return objs

@router.put("/{furniture_id}/images", response_model=List[schemas.FurnitureImageOut])
def replace_images(
    furniture_id: int,
    images: List[str],
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    """Reemplaza todas las imágenes del mueble por la lista proporcionada."""
    objs = crud_furniture.replace_images(db, furniture_id, images)
    return objs

@router.patch("/{furniture_id}/images/order", status_code=status.HTTP_204_NO_CONTENT)
def reorder_images(
    furniture_id: int,
    order: Dict[int, int],
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    """Reordena imágenes. Body: {image_id: new_position, ...}"""
    crud_furniture.reorder_images(db, furniture_id, order)
    return None

@router.delete("/{furniture_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    furniture_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserOut = Depends(auth.get_admin_user)
):
    """Elimina una imagen específica del mueble."""
    crud_furniture.delete_image(db, furniture_id, image_id)
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
