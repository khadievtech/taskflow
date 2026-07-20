"""
Централизованная конфигурация приложения.

Почему pydantic-settings, а не os.environ напрямую:
- валидация типов при старте (упадёт сразу, а не в рантайме на 200-м запросе)
- единая точка правды: все env-переменные видны в одном файле
- легко мокать в тестах через Settings(**overrides)

12-factor app принцип: конфигурация только через переменные окружения,
никаких хардкод-значений в коде.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Приложение
    app_name: str = "TaskFlow API"
    environment: str = "local"  # local | staging | production
    debug: bool = False

    # База данных (используется начиная с Phase 1)
    database_url: str = "postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow"

    # CORS — для локальной разработки с React на другом порту
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """
    Кэшируем настройки через lru_cache, чтобы не парсить env на каждый запрос,
    но при этом сохранить возможность override в тестах через dependency_overrides.
    """
    return Settings()
