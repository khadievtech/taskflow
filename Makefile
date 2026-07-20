.PHONY: help backend-install backend-run backend-test backend-lint

help:
	@echo "Доступные команды:"
	@echo "  make backend-install  — установить зависимости backend"
	@echo "  make backend-run      — запустить backend локально (без Docker)"
	@echo "  make backend-test     — прогнать тесты backend"
	@echo "  make backend-lint     — ruff + mypy"

backend-install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

backend-run:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && .venv/bin/pytest -v

backend-lint:
	cd backend && .venv/bin/ruff check app tests && .venv/bin/mypy app
