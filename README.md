# TaskFlow — Jira-like task management platform

[![CI](https://github.com/khadievtech/taskflow/actions/workflows/ci.yml/badge.svg)](https://github.com/khadievtech/taskflow/actions/workflows/ci.yml)

Pet-проект уровня Junior/Middle DevOps Engineer. Цель — пройти полный путь
от разработки до production-grade деплоя: Docker → CI/CD → Observability →
Kubernetes → IaC.

## Статус проекта

- [x] Phase 0 — Repo structure & app skeleton
- [x] Phase 0.5 — Postgres + SQLAlchemy + Alembic + Task CRUD
- [x] Phase 1 — Containerization (Docker Compose)
- [x] Phase 2 — CI (lint, test, build)
- [x] Phase 3 — CD (GHCR + деплой на home server)
- [~] Phase 4 — Observability
  - [x] 4a — метрики: инструментация, Prometheus, Grafana
  - [ ] 4b — логи: Loki
  - [ ] 4c — алерты: Alertmanager
- [ ] Phase 5 — Nginx + TLS
- [ ] Phase 6 — Auth (Keycloak)
- [ ] Phase 7 — Kubernetes
- [ ] Phase 8 — IaC (Terraform + Helm)
- [ ] Phase 9 — Async messaging (Kafka)
- [ ] Phase 10 — AWS migration

## Архитектура репозитория

Это **monorepo**: все сервисы (backend, frontend, infra-as-code) живут в одном
репозитории. Причина — на масштабе одного разработчика и tightly-coupled
docker-compose стека monorepo даёт атомарные коммиты через границы сервисов
и единый CI pipeline. Polyrepo имеет смысл, когда у сервисов независимые
команды-владельцы и релизные циклы — здесь пока не так.

Известные архитектурные решения — в [`docs/adr/`](docs/adr/README.md).
Известный технический долг — в [`docs/tech-debt.md`](docs/tech-debt.md).

```
taskflow/
├── backend/          # FastAPI application
├── frontend/          # React application
├── infra/             # Terraform, Helm charts, k8s manifests (позже)
├── docs/adr/           # Architecture Decision Records
├── .github/
│   └── workflows/      # CI/CD pipelines (Phase 2)
└── docker-compose.yml
```

## Запуск через Docker Compose (рекомендуемый способ)

Единственное требование — установленный Docker Desktop.

```bash
cp .env.example .env
docker compose up --build
```

Первый запуск соберёт образы (backend, frontend) и поднимет Postgres.
Backend при старте автоматически применит миграции (см. `backend/docker-entrypoint.sh`).

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Postgres: доступен с хоста на `localhost:5432` (для psql/DBeaver)

Остановить и удалить контейнеры (данные в volume сохранятся):
```bash
docker compose down
```

Остановить и **стереть данные БД** полностью:
```bash
docker compose down -v
```

Посмотреть логи конкретного сервиса:
```bash
docker compose logs -f backend
```

## Деплой на домашний сервер (Phase 3)

Образы собираются и публикуются в GHCR автоматически при мердже в `main`
(см. `.github/workflows/cd.yml`). Домашний сервер сам подтягивает новые
образы через **Watchtower** (pull-модель, без открытых портов наружу —
см. обоснование в истории обсуждения проекта).

**Одноразовая настройка перед первым деплоем:**
1. В GitHub: Settings → Secrets and variables → Actions → вкладка Variables →
   New repository variable → `PROD_API_URL` = `http://<IP-домашнего-сервера-в-локальной-сети>:8000`
2. После первого успешного запуска `cd.yml`: GitHub → Packages → открыть
   `taskflow-backend` и `taskflow-frontend` по отдельности → Package settings →
   Change visibility → **Public** (по умолчанию GHCR публикует пакеты
   приватными, даже если репозиторий публичный — иначе Watchtower не
   сможет скачать образ анонимно).

**На самом домашнем сервере** (Ubuntu, с установленным Docker):
```bash
git clone git@github.com:khadievtech/taskflow.git
cd taskflow
cp .env.prod.example .env.prod
nano .env.prod   # заполнить реальный IP сервера и пароль Grafana

# Общая сеть для стека приложения и стека мониторинга — создаётся один раз.
docker network create taskflow-shared

docker compose -p taskflow-prod -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Мониторинг (Phase 4)

Стек наблюдения живёт в отдельном compose-файле и подключается к той же
сети `taskflow-shared`. Причина разделения: система наблюдения должна
переживать сбои того, за чем наблюдает — если Prometheus падает вместе с
приложением, теряется именно та история метрик, которая нужна для разбора
инцидента.

```bash
docker compose -p taskflow-obs -f docker-compose.observability.yml --env-file .env.prod up -d
```

- Grafana: http://localhost:3000 (дашборд `TaskFlow API` создаётся автоматически)
- Prometheus: http://localhost:9090 (проверить цели: Status → Targets)
- Метрики приложения: http://localhost:8000/metrics

Дашборд построен по методике **четырёх золотых сигналов** (Google SRE):
traffic, errors, latency, saturation. Это те четыре вещи, с которых
начинают разбор любого инцидента.

Конфигурация Grafana задаётся файлами в `observability/grafana/provisioning`,
а не кликами в интерфейсе — источник данных и дашборд воспроизводятся
автоматически на любой машине.

Дальше обновления происходят сами: PR → merge → CI → CD собирает и
публикует образы → Watchtower на сервере находит новый тег в течение
минуты → перезапускает контейнер с новым образом.

## Git workflow

Trunk-Based Development:
- `main` — всегда деплоеспособен
- feature-ветки живут 1-3 дня: `feat/...`, `fix/...`, `chore/...`
- Conventional Commits для автоматического changelog/версионирования
- PR обязателен, прямые пуши в `main` запрещены (branch protection)
