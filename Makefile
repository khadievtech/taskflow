.PHONY: help backend-install backend-run backend-test backend-lint up down logs build

help:
	@echo "Доступные команды:"
	@echo "  make backend-install  — установить зависимости backend (без Docker)"
	@echo "  make backend-run      — запустить backend локально (без Docker)"
	@echo "  make backend-test     — прогнать тесты backend (без Docker)"
	@echo "  make backend-lint     — ruff + mypy (без Docker)"
	@echo "  make up               — поднять весь стек через docker compose"
	@echo "  make down             — остановить стек (данные БД сохранятся)"
	@echo "  make build            — пересобрать образы после изменения Dockerfile/зависимостей"
	@echo "  make logs              — логи всех сервисов (Ctrl+C для выхода)"

backend-install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

backend-run:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && .venv/bin/pytest -v

backend-lint:
	cd backend && .venv/bin/ruff check app tests && .venv/bin/mypy app

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f
