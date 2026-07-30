from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # Минимум 8 символов — нижняя граница из рекомендаций OWASP. Верхняя
    # граница нужна не для безопасности, а против отказа в обслуживании:
    # Argon2 намеренно вычислительно дорог, и без ограничения кто-то мог бы
    # прислать пароль на десять мегабайт и занять процессор.
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    # Схема ответа НЕ содержит hashed_password. Это главная причина держать
    # схемы Pydantic отдельно от моделей SQLAlchemy: если бы наружу отдавалась
    # модель, хеш пароля утекал бы в каждом ответе API.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
