# TaskFlow — Jira-like task management platform

Pet-проект уровня Junior/Middle DevOps Engineer. Цель — пройти полный путь
от разработки до production-grade деплоя: Docker → CI/CD → Observability →
Kubernetes → IaC.

## Статус проекта

- [x] Phase 0 — Repo structure & app skeleton
- [ ] Phase 1 — Containerization (Docker Compose)
- [ ] Phase 2 — CI (lint, test, build)
- [ ] Phase 3 — CD (GHCR + деплой на home server)
- [ ] Phase 4 — Observability (Prometheus/Grafana/Loki/Alertmanager)
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

```
taskflow/
├── backend/        # FastAPI application
├── frontend/        # React application
├── infra/           # Terraform, Helm charts, k8s manifests (позже)
├── .github/
│   └── workflows/    # CI/CD pipelines
└── docker-compose.yml (появится в Phase 1)
```

## Git workflow

Trunk-Based Development:
- `main` — всегда деплоеспособен
- feature-ветки живут 1-3 дня: `feat/...`, `fix/...`, `chore/...`
- Conventional Commits для автоматического changelog/версионирования
- PR обязателен, прямые пуши в `main` запрещены (branch protection)
