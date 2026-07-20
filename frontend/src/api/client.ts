// Все обращения к backend идут через одну точку — легко подменить
// базовый URL при переходе на Docker/Kubernetes, не трогая компоненты.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface HealthStatus {
  status: 'ok' | 'error';
}

export async function checkBackendHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_URL}/api/v1/health/ready`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return { status: 'error' };
    return (await response.json()) as HealthStatus;
  } catch {
    return { status: 'error' };
  }
}

export { API_URL };
