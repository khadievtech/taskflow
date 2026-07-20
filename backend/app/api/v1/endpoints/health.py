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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — намеренно широкий catch: любая
        # ошибка подключения к БД должна означать "под не готов принимать трафик"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable: {exc}",
        ) from exc
    return {"status": "ok"}
