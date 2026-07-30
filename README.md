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
- [x] Phase 4 — Observability
  - [x] 4a — метрики: инструментация, Prometheus, Grafana
  - [x] 4b — логи: структурированный JSON, Alloy, Loki
  - [x] 4c — алерты: Prometheus rules, Alertmanager, Telegram
- [~] Phase 5 — Nginx + TLS
  - [x] 5a — обратный прокси, единая точка входа
  - [ ] 5b — TLS (нужен домен для DNS-01)
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

## Приложение

Kanban-доска работает с реальным API: задачи создаются через форму,
переводятся между статусами кнопками, удаляются. Обрабатываются состояния
загрузки и ошибки — с возможностью повторить запрос.

```
frontend/src/
├── api/
│   ├── client.ts        # базовый путь API (относительный)
│   └── tasks.ts         # list / create / update / delete + разбор ошибок
├── hooks/useTasks.ts     # состояние списка, мутации без полного перезапроса
└── components/
    ├── CreateTaskForm.tsx  (+ тесты)
    ├── TaskCard.tsx        (+ тесты)
    ├── TaskBoard.tsx
    └── StatusPanel.tsx
```

Тесты фронтенда: `cd frontend && npm test` (vitest + jsdom +
@testing-library/react, 12 тестов, прогоняются в CI).

## Обратный прокси (Phase 5a)

Снаружи открыт единственный порт 80, за ним nginx маршрутизирует запросы:

```
http://<host>/           → frontend (статика)
http://<host>/api/...    → backend
http://<host>/metrics    → 404 (закрыто)
```

Что это меняет:

- **Порты сервисов больше не публикуются наружу.** Backend доступен на
  `127.0.0.1:8000` только для отладки с самой машины, frontend вообще не
  публикуется. Инструменты наблюдения (Grafana, Prometheus, Alertmanager,
  Loki, Alloy) привязаны к `127.0.0.1` и не видны из локальной сети.
- **CORS больше не участвует.** Фронтенд обращается к API относительными
  путями, то есть на тот же origin, что и страница.
- **Адрес backend не запекается в бандл.** Один образ работает в любом
  окружении, смена IP сервера не требует пересборки. В dev-режиме ту же роль
  играет `server.proxy` в `vite.config.ts`, поэтому dev и prod ведут себя
  одинаково.
- **Идентификатор запроса присваивает прокси.** Nginx передаёт `X-Request-ID`
  со значением встроенной переменной `$request_id`, а middleware приложения
  подхватывает его вместо генерации своего. Идентификатор рождается на границе
  системы и покрывает весь путь запроса.

Правка маршрутов не требует пересборки образа: конфиг лежит файлом в
`proxy/nginx.conf`, достаточно перечитать его —
`docker exec taskflow-prod-reverse-proxy-1 nginx -s reload`.

TLS отложен до появления домена: Let's Encrypt не выдаёт сертификаты на
приватные IP-адреса, а проверка HTTP-01 требует открытого наружу порта 80,
чего мы избегаем осознанно (см. `docs/adr/0002`). С доменом заработает
проверка DNS-01, которая портов не требует.

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
- Alertmanager: http://localhost:9093 (активные алерты, Silence)
- Alloy: http://localhost:12345 (граф конвейера логов — первое место для отладки)
- Метрики приложения: http://localhost:8000/metrics

Дашборд построен по методике **четырёх золотых сигналов** (Google SRE):
traffic, errors, latency, saturation. Это те четыре вещи, с которых
начинают разбор любого инцидента.

Конфигурация Grafana задаётся файлами в `observability/grafana/provisioning`,
а не кликами в интерфейсе — источники данных и дашборд воспроизводятся
автоматически на любой машине.

### Логи

Приложение пишет структурированные JSON-логи в stdout, Alloy читает их из
Docker и отправляет в Loki. Каждому запросу присваивается `request_id`,
он попадает в access-лог и возвращается клиенту в заголовке `X-Request-ID`.
При `DEBUG=true` тот же идентификатор появляется и в логах SQL-запросов.

Access-лог пишет `RequestContextMiddleware`, а не uvicorn: логгер uvicorn
работает на уровне ASGI-сервера, вне области видимости `ContextVar`, поэтому
`request_id` в его строки не попадает. Заодно middleware отдаёт отдельные
поля вместо текстовой строки:

```json
{"level":"INFO","logger":"app.access","message":"request completed",
 "request_id":"...","method":"GET","path":"/api/v1/tasks",
 "status_code":200,"duration_ms":4.71}
```

Полезные запросы в Grafana → Explore → Loki:

```
{service="backend"}                          все логи backend
{service="backend"} | level="ERROR"          только ошибки
{service="backend"} | json | duration_ms > 100    медленные запросы
{service="backend"} |= "trace-abc"           все строки одного запроса
{project="taskflow-prod"}                    логи всего стека приложения
```

`request_id` сознательно не является меткой Loki: он уникален для каждого
запроса, и метка из него породила бы миллионы потоков. Метками сделаны только
низкокардинальные поля — `level`, `logger`, `service`, `container`.

### Алерты

Правила в `observability/prometheus/rules/alerts.yml`, доставка через
Alertmanager в Telegram.

Настройка перед первым запуском:

```bash
# 1. Создать бота: написать @BotFather в Telegram, команда /newbot,
#    получить токен вида 123456789:AAH...
echo "ВАШ_ТОКЕН" > observability/alertmanager/telegram_token

# 2. Написать боту любое сообщение, затем узнать chat_id:
curl -s "https://api.telegram.org/botВАШ_ТОКЕН/getUpdates" | grep -o '"id":[-0-9]*' | head -1

# 3. Скопировать шаблон конфига и вписать chat_id
cp observability/alertmanager/alertmanager.yml.example observability/alertmanager/alertmanager.yml
nano observability/alertmanager/alertmanager.yml
```

Оба файла — `alertmanager.yml` и `telegram_token` — в `.gitignore`:
первый содержит персональный chat_id, второй секретный токен.

Текущие правила:

| Алерт | Условие | Severity |
|---|---|---|
| `BackendDown` | цель недоступна 2 мин | critical |
| `PostgresDown` | экспортёр недоступен 2 мин | critical |
| `HighErrorRate` | доля 5xx выше 5% в течение 5 мин | critical |
| `HighLatency` | p95 выше 500 мс в течение 10 мин | warning |
| `PostgresConnectionsHigh` | занято 80% соединений 10 мин | warning |

Все правила написаны на **симптомы**, которые ощущает пользователь, а не на
причины внутри системы. «Пятая часть запросов отвечает ошибкой» — алерт.
«Процесс перезапустился» — не алерт: если пользователи не заметили, будить
человека не за что. Каждое ложное срабатывание снижает доверие ко всей
системе оповещений, и через месяц шума реальный инцидент пропускают —
это alert fatigue.

Дальше обновления происходят сами: PR → merge → CI → CD собирает и
публикует образы → Watchtower на сервере находит новый тег в течение
минуты → перезапускает контейнер с новым образом.

## Git workflow

Trunk-Based Development:
- `main` — всегда деплоеспособен
- feature-ветки живут 1-3 дня: `feat/...`, `fix/...`, `chore/...`
- Conventional Commits для автоматического changelog/версионирования
- PR обязателен, прямые пуши в `main` запрещены (branch protection)
