from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware

settings = get_settings()

# Настраиваем логирование до создания приложения, чтобы сообщения самого
# старта (включая логи uvicorn) уже были в JSON.
setup_logging("DEBUG" if settings.debug else "INFO", sql_echo=settings.debug)

app = FastAPI(
    title=settings.app_name,
    # В production скрываем автогенерируемую документацию,
    # чтобы не светить внутреннюю структуру API наружу
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

# Порядок регистрации важен: Starlette выполняет middleware в порядке,
# обратном добавлению, поэтому RequestIdMiddleware добавляем последним —
# так он окажется самым внешним, и request_id будет доступен уже в CORS-слое
# и во всех логах, включая логи об ошибках.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

app.include_router(api_router)

# Инструментация Prometheus.
#
# Что даёт из коробки: счётчик запросов и гистограмма латентности с разбивкой
# по методу, пути и коду ответа. Именно гистограмма (а не среднее) позволяет
# считать перцентили — p95/p99 показывают опыт худших запросов, тогда как
# среднее их полностью скрывает.
#
# should_group_status_codes=False — не склеивать 500 и 503 в группу "5xx".
# Разница принципиальна при разборе инцидента: 503 обычно означает, что
# зависимость недоступна, а 500 — необработанное исключение в коде.
#
# excluded_handlers — не собираем метрики о самом /metrics, иначе Prometheus
# своими же обращениями искусственно раздувает счётчики запросов.
#
# Про бакеты гистограммы и кардинальность:
# в Prometheus каждая комбинация меток — отдельный временной ряд, и число
# рядов гистограммы = бакеты × хендлеры × методы. Библиотека по умолчанию даёт
# per-handler гистограмме всего 3 бакета (0.1, 0.5, 1), чтобы защитить большие
# API от взрыва кардинальности — но тогда перцентили бесполезны для быстрого
# API: всё быстрее 100 мс схлопывается в первый бакет.
#
# У нас ~6 эндпоинтов, поэтому тонкие бакеты обходятся дёшево и дают реальные
# p95/p99 по каждому эндпоинту. На API из 200 ручек так делать не стоит —
# там правильнее оставить дефолт и смотреть перцентили по highr-гистограмме.
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics"],
).add(
    metrics.default(latency_lowr_buckets=LATENCY_BUCKETS)
).instrument(app).expose(app, include_in_schema=False)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "environment": settings.environment}
