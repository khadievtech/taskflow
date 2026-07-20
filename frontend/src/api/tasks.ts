export type TaskStatus = 'todo' | 'in_progress' | 'done';

export interface Task {
  id: string;
  title: string;
  assignee: string;
  status: TaskStatus;
}

// Заглушка до Phase 1 (Postgres + реальный /api/v1/tasks эндпоинт).
// Формат такой же, каким будет ответ API — чтобы замена на реальные
// данные не требовала переписывать компоненты.
export const MOCK_TASKS: Task[] = [
  { id: 'TF-1', title: 'Настроить структуру монорепозитория', assignee: 'you', status: 'done' },
  { id: 'TF-2', title: 'Собрать backend-скелет FastAPI', assignee: 'you', status: 'done' },
  { id: 'TF-3', title: 'Собрать frontend-скелет React + Vite', assignee: 'you', status: 'in_progress' },
  { id: 'TF-4', title: 'Подключить Postgres + Alembic миграции', assignee: 'you', status: 'todo' },
  { id: 'TF-5', title: 'Docker Compose для всего стека', assignee: 'you', status: 'todo' },
];
