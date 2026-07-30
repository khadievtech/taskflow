import { useCallback, useEffect, useState } from 'react';
import {
  fetchMe,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  type Credentials,
  type User,
} from '../api/auth';

export type AuthState = 'checking' | 'authenticated' | 'anonymous';

/**
 * Состояние аутентификации.
 *
 * Единственный источник правды — ответ /auth/me. Токен лежит в httpOnly
 * cookie, недоступной JavaScript, поэтому определить "вошёл ли я" локально
 * невозможно: нужно спросить сервер.
 *
 * Это не недостаток, а следствие выбора в пользу защиты от XSS. Плюс подход
 * честнее: локальный флаг мог бы говорить "вошёл", когда токен уже истёк.
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [state, setState] = useState<AuthState>('checking');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await fetchMe();
        if (!cancelled) {
          setUser(me);
          setState('authenticated');
        }
      } catch {
        // 401 здесь — нормальный путь, а не ошибка: значит пользователь не
        // вошёл. Показывать сообщение об ошибке было бы неверно.
        if (!cancelled) {
          setUser(null);
          setState('anonymous');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (creds: Credentials) => {
    setUser(await apiLogin(creds));
    setState('authenticated');
  }, []);

  const signUp = useCallback(async (creds: Credentials) => {
    setUser(await apiRegister(creds));
    setState('authenticated');
  }, []);

  const signOut = useCallback(async () => {
    await apiLogout();
    setUser(null);
    setState('anonymous');
  }, []);

  return { user, state, signIn, signUp, signOut };
}
