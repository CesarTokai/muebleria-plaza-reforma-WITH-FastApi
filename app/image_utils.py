import base64
import binascii
from typing import Optional, Tuple
from fastapi import HTTPException

_MAX_IMG_BYTES = 2 * 1024 * 1024  # 2 MB
_ALLOWED_IMG_MIME_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,")


def _strip_data_url_prefix(b64: str) -> Tuple[str, Optional[str]]:
    for p in _ALLOWED_IMG_MIME_PREFIXES:
        if b64.startswith(p):
            return b64[len(p):], p.split(";")[0].split(":")[1]
    return b64, None


def validate_base64_image(b64: Optional[str]) -> Optional[str]:
    """Valida que una cadena base64 represente una imagen y no exceda el tamaño permitido.

    Retorna la cadena original si es None o válida. Lanza HTTPException con código 400
    para base64 inválido o 413 si el tamaño excede el máximo.
    """
    if not b64:
        return None
    original = b64.strip()
    payload, _mime = _strip_data_url_prefix(original)
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Imagen en base64 inválida")

    if len(raw) > _MAX_IMG_BYTES:
        raise HTTPException(status_code=413, detail=f"La imagen excede {_MAX_IMG_BYTES // (1024*1024)}MB")
    return original
