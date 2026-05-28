# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=20, 
        description="Никнейм от 3 до 20 символов (латиница, цифры, _ -)",
        pattern=r"^[a-zA-Z0-9_-]+$"  # <-- Строгий регекс
    )
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)
    password_confirm: str

    @model_validator(mode='before')
    def check_passwords_match(cls, values):
        """Проверяет, что пароли совпадают, до создания объекта"""
        if values.get('password') != values.get('password_confirm'):
            raise ValueError("Passwords do not match")
        return values

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "cool_gamer_99",
            "email": "user@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!"
        }
    })


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Схема ответа (без паролей)"""
    id: int
    username: str
    email: EmailStr
    avatar_url: str
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)