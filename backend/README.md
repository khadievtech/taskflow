# TaskFlow Backend

FastAPI-приложение. На Phase 0 — только health-check эндпоинты, без БД.

## Локальный запуск (без Docker, для разработки)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Проверка: http://localhost:8000/docs

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
