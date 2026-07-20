import { StatusPanel } from './components/StatusPanel';
import { TaskBoard } from './components/TaskBoard';

export function App() {
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
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-3)' }}>
          <h1 style={{ fontSize: 22 }}>TaskFlow</h1>
          <span className="mono" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            v0.1.0 · phase 0
          </span>
        </div>
        <StatusPanel />
      </header>

      <main>
        <TaskBoard />
      </main>
    </div>
  );
}

export default App;
