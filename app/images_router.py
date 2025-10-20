from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from . import database, models
import io

router = APIRouter(prefix="/images", tags=["images"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{image_id}/content")
def get_image_content(image_id: int, db: Session = Depends(get_db)):
    """Retorna el contenido binario de la imagen (stream) con el MIME correcto."""
    img = db.query(models.FurnitureImage).filter(models.FurnitureImage.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    # usar StreamingResponse para no cargar en memoria adicional
    try:
        stream = io.BytesIO(img.bytes)
        headers = {"Content-Length": str(img.size_bytes)}
        return StreamingResponse(stream, media_type=img.mime, headers=headers)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al leer el contenido de la imagen")

