from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from ..models.user import User
from ..core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from ..schemas.auth import UserCreate, UserResponse

async def register_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    # Проверка на существующего пользователя
    stmt = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким логином или почтой уже существует"
        )
    
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароли не совпадают"
        )

    # Проверка длины пароля ДО хэширования (bcrypt лимит)
    if len(user_data.password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль не может быть длиннее 72 символов"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        avatar_url="/avatars/default1.png",  # дефолтная аватарка
        role="unverified",
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)

async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> dict:
    stmt = select(User).where(
        (User.username == username_or_email) | (User.email == username_or_email)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные"
        )
        
    return {
        "user": UserResponse.model_validate(user),
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id))
    }