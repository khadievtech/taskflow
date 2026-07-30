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

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Значение по умолчанию для локальной разработки. Вынесено в константу, чтобы
# валидатор ниже мог сравнить с ним и не дать запустить production с этим
# ключом. Утечка ключа означает, что кто угодно подпишет токен от любого
# пользователя — то есть полный обход аутентификации.
DEV_JWT_SECRET = "dev-only-insecure-secret-change-me"


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

    # CORS. После введения обратного прокси (Phase 5a) фронтенд и API живут
    # на одном origin, поэтому CORS фактически не участвует. Настройка
    # оставлена для случая, когда фронтенд запускают отдельно от прокси.
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Аутентификация ---

    jwt_secret_key: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"

    # Семь дней. Компромисс: короткий срок жизни безопаснее (украденный токен
    # быстрее истекает), но заставляет пользователя часто входить заново.
    # Правильное решение для короткоживущих токенов — refresh-токены, но это
    # отдельный механизм со своей сложностью (ротация, отзыв, хранение).
    access_token_expire_minutes: int = 60 * 24 * 7

    # Флаг Secure у cookie означает "передавать только по HTTPS". Пока TLS нет
    # (Phase 5b), флаг выключен — иначе браузер не отправлял бы cookie вообще.
    # ОБЯЗАТЕЛЬНО включить после появления HTTPS.
    cookie_secure: bool = False

    # Позволяет закрыть регистрацию после создания своей учётной записи.
    # Открытая регистрация означает, что любой, кто дошёл до формы, получит
    # доступ — на домашнем сервере это стоит выключить сразу после первого
    # входа.
    allow_registration: bool = True

    @model_validator(mode="after")
    def _forbid_dev_secret_in_production(self) -> "Settings":
        """
        Отказ стартовать в production с ключом по умолчанию.

        Проверка при старте, а не в рантайме: приложение с известным всем
        секретом лучше не запустить вообще, чем запустить и позволить любому
        подделать токен. Такие ошибки иначе обнаруживаются уже после утечки.
        """
        if self.environment == "production" and self.jwt_secret_key == DEV_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY не задан. Сгенерировать: "
                "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Кэшируем настройки через lru_cache, чтобы не парсить env на каждый запрос,
    но при этом сохранить возможность override в тестах через dependency_overrides.
    """
    return Settings()
