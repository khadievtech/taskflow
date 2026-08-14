# Kubernetes (Phase 7)

Локальный кластер через `kind` — три узла, полный (не облегчённый) Kubernetes,
тот же API, что и в управляемых облачных кластерах.

## Создать кластер

```bash
kind create cluster --config infra/kind/cluster.yaml
```

Порты 8080/8443 на хосте проброшены на 80/443 внутрь кластера (для Ingress,
Phase 7b). Порт 80 занят обратным прокси из Docker Compose, поэтому не 80.

## Подготовить секреты (не в git)

```bash
cp infra/k8s/base/10-postgres-secret.example.yaml infra/k8s/base/10-postgres-secret.yaml
# отредактировать пароль

cp infra/k8s/base/41-backend-secret.yaml.example infra/k8s/base/41-backend-secret.yaml
# подставить DATABASE_URL с паролем и JWT_SECRET_KEY
```

Оба файла в `.gitignore` — как и Secret в Kubernetes, значения в них
кодируются base64, а не шифруются (см. комментарий в самом манифесте).

## Применить

```bash
kubectl apply -f infra/k8s/base/
```

Порядок важен только для Namespace — остальное `kubectl` разрешает по
зависимостям автоматически. Числовые префиксы в именах файлов — просто
чтобы `kubectl apply -f каталог/` (применяет по алфавиту) не упёрся в
Namespace, ещё не созданный.

## Что внутри

| Файл | Объект | Зачем |
|---|---|---|
`00-namespace` | Namespace | Изоляция объектов приложения от системных |
`10-postgres-secret` | Secret | Пароль БД |
`20-postgres-service` | Service (headless) | Постоянное DNS-имя для БД |
`30-postgres-statefulset` | StatefulSet | БД с устойчивым томом на пересоздание пода |
`40-backend-config` | ConfigMap | Несекретные настройки backend |
`41-backend-secret` | Secret | `DATABASE_URL`, `JWT_SECRET_KEY` |
`50-migrate-job` | Job | Миграции Alembic — ровно один раз, не в каждом поде |
`60-backend-deployment` | Deployment | 2 реплики API, rolling update без простоя |
`61-backend-service` | Service | Балансировка между репликами backend |

## Проверить руками (пока нет Ingress)

```bash
kubectl port-forward -n taskflow svc/backend 8001:8000
```

В другом окне:
```bash
curl http://localhost:8001/api/v1/health/ready
```

`port-forward` держит соединение с конкретным подом на момент запуска и
обрывается при его пересоздании (например, после `rollout restart`) — команду
нужно запускать заново. Это временное неудобство до появления Ingress.

## Изменить настройку в ConfigMap

ConfigMap не перезапускает поды автоматически — приложение читает
переменные окружения один раз при старте.

```bash
kubectl patch configmap backend -n taskflow --type merge -p '{"data":{"KEY":"value"}}'
kubectl rollout restart deployment/backend -n taskflow
kubectl rollout status deployment/backend -n taskflow
```

## Применить новую миграцию

Имя Job уникально — повторное применение манифеста с тем же именем
завершится ошибкой:

```bash
kubectl delete job migrate -n taskflow --ignore-not-found
kubectl apply -f infra/k8s/base/50-migrate-job.yaml
kubectl logs -n taskflow job/migrate
```

На Phase 8 (Helm) это решается hook-аннотацией `helm.sh/hook: pre-upgrade`.

## Удалить кластер

```bash
kind delete cluster --name taskflow
```

Полностью уничтожает все три контейнера-узла вместе с данными — для
пересборки с нуля, если что-то пошло не так.
