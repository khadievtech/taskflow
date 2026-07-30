import { useCallback, useEffect, useState } from 'react';
import {
  createTask as apiCreate,
  deleteTask as apiDelete,
  listTasks,
  updateTask as apiUpdate,
  type Task,
  type TaskCreate,
  type TaskStatus,
} from '../api/tasks';

export type LoadState = 'loading' | 'ready' | 'error';

/**
 * Хук работы со списком задач.
 *
 * Почему обычные useState/useEffect, а не TanStack Query: на четыре операции
 * и один список библиотека принесла бы больше концепций (ключи запросов,
 * инвалидация кэша, состояния fetching/stale), чем пользы. При появлении
 * нескольких экранов, шарящих одни данные, или необходимости фонового
 * обновления — переход на TanStack Query оправдан, и он делается локально,
 * не затрагивая компоненты.
 *
 * Мутации не перезапрашивают весь список: API возвращает изменённую задачу,
 * и она подставляется в локальное состояние. Это экономит запрос и, важнее,
 * не даёт списку "прыгнуть" из-за одновременных изменений.
 */
export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setState('loading');
    setError(null);
    try {
      setTasks(await listTasks());
      setState('ready');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить задачи');
      setState('error');
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const create = useCallback(async (data: TaskCreate) => {
    const created = await apiCreate(data);
    setTasks((prev) => [created, ...prev]);
  }, []);

  const changeStatus = useCallback(async (id: string, status: TaskStatus) => {
    const updated = await apiUpdate(id, { status });
    setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
  }, []);

  const remove = useCallback(async (id: string) => {
    await apiDelete(id);
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return { tasks, state, error, reload, create, changeStatus, remove };
}
