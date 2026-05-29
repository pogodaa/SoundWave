# backend/app/api/v1/users.py
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Папка для загруженных аватаров (создаётся при первой загрузке)
AVATARS_DIR = Path(__file__).resolve().parents[3] / "static" / "avatars"
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о текущем авторизованном пользователе"""
    return current_user


@router.patch("/me/avatar", response_model=UserRead)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить аватар текущего пользователя"""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допустимы только изображения: JPEG, PNG, GIF, WebP",
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 5 МБ",
        )

    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    extension = ext_map.get(file.content_type, ".jpg")
    filename = f"{uuid.uuid4().hex}{extension}"

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = AVATARS_DIR / filename
    file_path.write_bytes(content)

    current_user.avatar_url = f"/static/avatars/{filename}"
    await db.commit()
    await db.refresh(current_user)

    return current_user
