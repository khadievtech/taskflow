"""
Health-check endpoints.

Разделяем liveness и readiness сразу — это пригодится в Kubernetes (Phase 7):
- liveness:  "процесс жив, не нужно рестартовать под" — не должен зависеть от БД
- readiness: "под готов принимать трафик" — здесь как раз проверяем зависимости
  (БД, Redis и т.д.), когда они появятся

Если сделать один общий /health, который дергает БД, то временная просадка
БД вызовет CrashLoopBackOff всех подов вместо простого исключения их из
балансировки — это частая ошибка новичков в K8s.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    # TODO(Phase 1): добавить проверку подключения к Postgres/Redis
    return {"status": "ok"}
