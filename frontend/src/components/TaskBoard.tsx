import type { TaskStatus } from '../api/tasks';
import { useTasks } from '../hooks/useTasks';
import { CreateTaskForm } from './CreateTaskForm';
import { TaskCard } from './TaskCard';

const COLUMNS: { key: TaskStatus; label: string; accent: string }[] = [
  { key: 'todo', label: 'To do', accent: 'var(--color-text-muted)' },
  { key: 'in_progress', label: 'In progress', accent: 'var(--color-warn)' },
  { key: 'done', label: 'Done', accent: 'var(--color-success)' },
];

export function TaskBoard() {
  const { tasks, state, error, reload, create, changeStatus, remove } = useTasks();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <CreateTaskForm onCreate={create} />

      {/* Три состояния загрузки обрабатываются явно. Показывать пустую доску
          во время загрузки — значит вводить в заблуждение: пользователь решит,
          что задач нет, тогда как данные просто ещё не пришли. */}
      {state === 'loading' && (
        <span className="mono" style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          загрузка задач…
        </span>
      )}

      {state === 'error' && (
        <div
          role="alert"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: 'var(--space-3)',
            border: '1px solid #e5484d',
            borderRadius: 'var(--radius-sm)',
            fontSize: 13,
          }}
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => void reload()}
            style={{
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text)',
              cursor: 'pointer',
              fontSize: 12,
              padding: '4px 10px',
            }}
          >
            Повторить
          </button>
        </div>
      )}

      {state === 'ready' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, minmax(220px, 1fr))',
            gap: 'var(--space-4)',
            alignItems: 'start',
          }}
        >
          {COLUMNS.map((col) => {
            const items = tasks.filter((t) => t.status === col.key);
            return (
              <div
                key={col.key}
                style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span
                    style={{ width: 6, height: 6, borderRadius: '50%', background: col.accent }}
                  />
                  <h3
                    style={{
                      fontSize: 13,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    {col.label}
                  </h3>
                  <span
                    className="mono"
                    style={{ fontSize: 11, color: 'var(--color-text-muted)' }}
                  >
                    {items.length}
                  </span>
                </div>

                <div
                  style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}
                >
                  {items.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onChangeStatus={changeStatus}
                      onRemove={remove}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
