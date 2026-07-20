"""
Явный реэкспорт всех моделей — критично для Alembic autogenerate.

SQLAlchemy строит Base.metadata только из тех классов, которые были
импортированы хоть раз. Если забыть импортировать новую модель здесь,
Alembic просто не увидит новую таблицу и autogenerate предложит её удалить.
Это одна из самых частых ошибок при работе с Alembic.
"""

from app.models.task import Task, TaskStatus

__all__ = ["Task", "TaskStatus"]
