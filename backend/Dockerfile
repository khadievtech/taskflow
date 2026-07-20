# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app


# ---------------------------------------------------------------------------
# dev — используется в docker-compose.yml для локальной разработки.
# Код реального приложения перекрывается bind-mount'ом из compose, поэтому
# здесь COPY . . нужен только для того, чтобы `pip install -e .` смог
# собрать метаданные пакета (hatchling требует физического наличия app/).
# ---------------------------------------------------------------------------
FROM base AS dev
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ---------------------------------------------------------------------------
# builder — собирает зависимости в изолированный --user site-packages,
# чтобы в production-образ попал только результат, без pip-кэша и build-инструментов.
#
# Известное упрощение: слой install здесь инвалидируется при любом изменении
# app/ (COPY . . перед RUN), т.к. зависимости не вынесены в отдельный lock-файл.
# Для проекта такого размера это приемлемо; на большем масштабе — вынести
# зависимости в requirements.txt/uv.lock и копировать его отдельным слоем
# до копирования кода, чтобы pip install кэшировался независимо от кода.
# ---------------------------------------------------------------------------
FROM base AS builder
COPY . .
RUN pip install --no-cache-dir --user .


# ---------------------------------------------------------------------------
# production — минимальный слой поверх base: только зависимости, код,
# непривилегированный пользователь. Пригодится в Phase 3 (сборка образа
# в GitHub Actions и публикация в GHCR).
# ---------------------------------------------------------------------------
FROM base AS production
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && chown -R appuser:appuser /app
ENV PATH=/home/appuser/.local/bin:$PATH
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')" || exit 1
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
