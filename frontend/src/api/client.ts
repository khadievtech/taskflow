// Обращения к API идут ОТНОСИТЕЛЬНЫМИ путями, без указания хоста.
//
// Почему так, а не через VITE_API_URL с абсолютным адресом:
// 1. Vite подставляет значение переменной прямо в JS-бандл на этапе сборки.
//    Абсолютный адрес пришлось бы фиксировать при сборке образа, и один и
//    тот же образ нельзя было бы использовать в разных окружениях. Смена IP
//    домашнего сервера требовала бы пересборки.
// 2. Относительный путь работает в любом окружении без изменений: маршрут
//    /api/... разбирает nginx в production и dev-прокси Vite в разработке.
// 3. Запрос идёт на тот же origin, что и страница, поэтому CORS не участвует.
//
// Переопределение через VITE_API_URL оставлено для нештатных случаев —
// например, если фронтенд понадобится указать на удалённый backend, минуя
// прокси. По умолчанию пусто, то есть относительный путь.
const API_BASE = import.meta.env.VITE_API_URL ?? '';

export interface HealthStatus {
  status: 'ok' | 'error';
}

export async function checkBackendHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health/ready`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return { status: 'error' };
    return (await response.json()) as HealthStatus;
  } catch {
    return { status: 'error' };
  }
}

export { API_BASE };
