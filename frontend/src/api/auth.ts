import { API_BASE } from './client';
import { ApiError } from './tasks';

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Credentials {
  email: string;
  password: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      // Pydantic при ошибке валидации отдаёт detail массивом объектов,
      // а не строкой — иначе в интерфейсе появилось бы "[object Object]".
      if (typeof body?.detail === 'string') detail = body.detail;
      else if (Array.isArray(body?.detail)) detail = 'Проверьте корректность полей';
    } catch {
      // тело не JSON — оставляем код статуса
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// Токен приходит в httpOnly cookie, поэтому здесь нет ни его чтения, ни
// сохранения: браузер сам приложит cookie к следующим запросам. JavaScript
// доступа к значению не имеет — в этом и смысл httpOnly.
export const register = (creds: Credentials) =>
  request<User>('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(creds) });

export const login = (creds: Credentials) =>
  request<User>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(creds) });

export const logout = () => request<void>('/api/v1/auth/logout', { method: 'POST' });

export const fetchMe = () => request<User>('/api/v1/auth/me');
