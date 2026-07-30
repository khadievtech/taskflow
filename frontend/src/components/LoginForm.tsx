import { useState } from 'react';
import type { Credentials } from '../api/auth';

interface Props {
  onSignIn: (creds: Credentials) => Promise<void>;
  onSignUp: (creds: Credentials) => Promise<void>;
}

const inputStyle: React.CSSProperties = {
  background: 'var(--color-surface-raised)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text)',
  padding: '9px 11px',
  fontSize: 13,
  fontFamily: 'inherit',
  width: '100%',
};

export function LoginForm({ onSignIn, onSignUp }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Требование к длине пароля повторяет min_length в схеме UserCreate.
  // Проверка на клиенте не заменяет серверную, а избавляет от лишнего запроса
  // и даёт понятную подсказку до отправки.
  const passwordTooShort = mode === 'register' && password.length > 0 && password.length < 8;
  const invalid =
    email.trim().length === 0 || password.length === 0 || passwordTooShort;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (invalid || busy) return;

    setBusy(true);
    setError(null);
    try {
      const creds = { email: email.trim(), password };
      await (mode === 'login' ? onSignIn(creds) : onSignUp(creds));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось выполнить вход');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 340, margin: '0 auto', paddingTop: 'var(--space-8)' }}>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <h2 style={{ fontSize: 16 }}>{mode === 'login' ? 'Вход' : 'Регистрация'}</h2>

        <input
          aria-label="Email"
          type="email"
          autoComplete="email"
          placeholder="email@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={busy}
          style={inputStyle}
        />

        <input
          aria-label="Пароль"
          type="password"
          // Подсказка браузеру, какой пароль предлагать: current-password для
          // входа, new-password для регистрации — иначе менеджер паролей
          // предложит сохранить существующий вместо генерации нового.
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
          style={inputStyle}
        />

        {passwordTooShort && (
          <span style={{ fontSize: 12, color: 'var(--color-warn)' }}>
            Минимум 8 символов
          </span>
        )}

        <button
          type="submit"
          disabled={invalid || busy}
          style={{
            background: invalid || busy ? 'var(--color-surface-raised)' : 'var(--color-accent)',
            color: invalid || busy ? 'var(--color-text-muted)' : '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 16px',
            fontSize: 13,
            fontWeight: 500,
            cursor: invalid || busy ? 'not-allowed' : 'pointer',
          }}
        >
          {busy ? 'Отправляем…' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
        </button>

        {error && (
          <span role="alert" style={{ fontSize: 12, color: '#e5484d' }}>
            {error}
          </span>
        )}

        <button
          type="button"
          onClick={() => {
            setMode(mode === 'login' ? 'register' : 'login');
            setError(null);
          }}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            fontSize: 12,
            padding: 0,
            textAlign: 'left',
          }}
        >
          {mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </form>
    </div>
  );
}
