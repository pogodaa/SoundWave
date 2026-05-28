# backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase, registry

# Создаём registry для управления моделями
mapper_registry = registry()

class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    registry = mapper_registry
    metadata = mapper_registry.metadata