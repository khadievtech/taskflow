import { useAuth } from './hooks/useAuth';
import { LoginForm } from './components/LoginForm';
import { StatusPanel } from './components/StatusPanel';
import { TaskBoard } from './components/TaskBoard';
import { version } from '../package.json';

export function App() {
  const { user, state, signIn, signUp, signOut } = useAuth();

  return (
    <div
      style={{
        maxWidth: 960,
        margin: '0 auto',
        padding: 'var(--space-8) var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-6)',
      }}
    >
      <header style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--space-3)',
            flexWrap: 'wrap',
          }}
        >
          <h1 style={{ fontSize: 22 }}>TaskFlow</h1>
          {/* Версия берётся из package.json на этапе сборки, а не пишется
              руками: захардкоженная строка неизбежно расходится с реальностью.
              Раньше здесь месяцами висело "phase 0". */}
          <span className="mono" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            v{version}
          </span>

          {user && (
            <div
              style={{
                marginLeft: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
              }}
            >
              <span className="mono" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                {user.email}
              </span>
              <button
                type="button"
                onClick={() => void signOut()}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--color-text-muted)',
                  cursor: 'pointer',
                  fontSize: 12,
                  padding: '4px 10px',
                }}
              >
                Выйти
              </button>
            </div>
          )}
        </div>
        <StatusPanel />
      </header>

      <main>
        {/* Состояние checking обрабатывается отдельно: без него при загрузке
            на мгновение показалась бы форма входа даже вошедшему пользователю. */}
        {state === 'checking' && (
          <span className="mono" style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            проверяем сессию…
          </span>
        )}
        {state === 'anonymous' && <LoginForm onSignIn={signIn} onSignUp={signUp} />}
        {state === 'authenticated' && <TaskBoard />}
      </main>
    </div>
  );
}

export default App;
