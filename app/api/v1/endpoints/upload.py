import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from app.api import deps

router = APIRouter()

# Directory to save uploaded files, relative to where uvicorn runs (the backend root)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 5
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Magic-byte signatures mapped to MIME type
_MAGIC: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}
_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def _detect_mime(data: bytes) -> str | None:
    """Identify image type from file magic bytes (ignores user-supplied content_type)."""
    for sig, mime in _MAGIC.items():
        if data.startswith(sig):
            return mime
    # WebP: bytes 0-3 = 'RIFF', bytes 8-11 = 'WEBP'
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_admin=Depends(deps.get_current_admin),
):
    """Upload a single image and return its public URL. Admin only."""
    contents = await file.read()

    # Validate size before anything else
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed: {MAX_FILE_SIZE_MB} MB.",
        )

    # Validate actual file type via magic bytes – never trust user-supplied content_type
    actual_mime = _detect_mime(contents)
    if actual_mime is None or actual_mime not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid image (jpeg, png, webp, or gif).",
        )

    ext = _MIME_TO_EXT[actual_mime]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    url = f"/uploads/{filename}"
    return {"url": url}
