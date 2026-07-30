import { API_BASE } from './client';

export type TaskStatus = 'todo' | 'in_progress' | 'done';

// Типы повторяют схемы Pydantic из backend/app/schemas/task.py.
// Держать их синхронными вручную — известная слабость такого подхода: при
// изменении схемы на бэкенде фронтенд об этом не узнает до рантайма.
// В зрелом проекте типы генерируют из OpenAPI-схемы FastAPI (openapi-typescript
// или orval), и расхождение ловится на этапе сборки. Для трёх интерфейсов
// ручная синхронизация дешевле генератора — см. tech-debt.
export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  assignee: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string | null;
  assignee?: string | null;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  assignee?: string | null;
}

export class ApiError extends Error {
  // Поле объявлено отдельно, а не как параметр-свойство конструктора:
  // шаблон Vite включает флаг erasableSyntaxOnly, который запрещает синтаксис,
  // генерирующий код во время выполнения. Требование в том, чтобы типы
  // стирались без следа — параметры-свойства этому не удовлетворяют.
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });

  if (!response.ok) {
    // FastAPI возвращает подробности в поле detail. Пытаемся его прочитать,
    // но не падаем, если тело не JSON — например, при 502 от прокси, когда
    // ответ формирует nginx, а не приложение.
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // тело не JSON — оставляем код статуса как сообщение
    }
    throw new ApiError(detail, response.status);
  }

  // 204 No Content не имеет тела, и response.json() на нём упал бы.
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const listTasks = () => request<Task[]>('/api/v1/tasks');

export const createTask = (data: TaskCreate) =>
  request<Task>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(data) });

export const updateTask = (id: string, patch: TaskUpdate) =>
  request<Task>(`/api/v1/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });

export const deleteTask = (id: string) =>
  request<void>(`/api/v1/tasks/${id}`, { method: 'DELETE' });
