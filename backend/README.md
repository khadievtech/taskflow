# TaskFlow Backend

FastAPI-приложение. На Phase 0 — только health-check эндпоинты, без БД.

## Локальный запуск (без Docker, для разработки)

Нужен локальный Postgres (до Phase 1 с Docker Compose — ставим руками):

```bash
sudo apt install postgresql
sudo -u postgres psql -c "CREATE USER taskflow WITH PASSWORD 'taskflow';"
sudo -u postgres psql -c "CREATE DATABASE taskflow OWNER taskflow;"
```

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head             # применяет миграции к БД
uvicorn app.main:app --reload --port 8000
```

Проверка: http://localhost:8000/docs

## Миграции

```bash
alembic revision --autogenerate -m "описание изменения"   # сгенерировать миграцию
# ВСЕГДА открыть и проверить файл в alembic/versions/ перед применением —
# autogenerate это черновик, не истина в последней инстанции
alembic upgrade head                                        # применить
alembic downgrade -1                                         # откатить на одну версию назад
alembic current                                              # текущая версия БД
alembic history                                              # вся история миграций
```

## Известный технический долг

Тесты сейчас используют ту же БД, что и локальная разработка (`DATABASE_URL`
из `.env`) — это временно и будет исправлено на Phase 1: отдельный
`postgres-test` сервис в Docker Compose + откат транзакции после каждого
теста (через фикстуру `session` с rollback вместо commit). Если запускать
тесты сейчас, они реально пишут и читают из вашей dev-БД.

## Команды разработки

```bash
ruff check app tests      # линтер
ruff format app tests      # автоформатирование
mypy app                  # проверка типов
pytest -v                 # тесты
```

## Структура

```
app/
├── main.py           # точка входа, создание FastAPI app
├── core/config.py    # настройки через pydantic-settings (12-factor)
├── api/v1/           # версионированный API
│   ├── router.py
│   └── endpoints/
├── models/            # SQLAlchemy ORM модели (Phase 1)
├── schemas/           # Pydantic-схемы для запросов/ответов
├── db/                # сессии, engine (Phase 1)
└── services/          # бизнес-логика, отделённая от роутов
```

Почему `services/` отдельно от `endpoints/`: роуты не должны содержать
бизнес-логику напрямую — это усложняет тестирование (пришлось бы поднимать
весь HTTP-стек ради unit-теста) и переиспользование (например, та же логика
понадобится в Kafka-консьюмере на Phase 9).
