#!/bin/sh
set -e

# depends_on: condition: service_healthy в docker-compose.yml уже гарантирует,
# что Postgres принимает соединения к этому моменту — здесь не нужен свой
# retry-loop поверх него, просто применяем миграции и стартуем приложение.
#
# Важная оговорка на будущее (Phase 7, Kubernetes): при нескольких репликах
# backend этот entrypoint выполнит `alembic upgrade head` в КАЖДОМ поде
# одновременно — для одной миграции это обычно безвредно (Alembic использует
# advisory lock в Postgres), но правильная production-практика — выносить
# миграции в отдельный Job/init-container, выполняемый один раз перед
# раскаткой новых реплик. Сейчас, с одним контейнером backend, это не проблема.

echo "Applying database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
