import { useState } from 'react';
import type { Task, TaskStatus } from '../api/tasks';

const ORDER: TaskStatus[] = ['todo', 'in_progress', 'done'];

interface Props {
  task: Task;
  onChangeStatus: (id: string, status: TaskStatus) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
}

const iconButton: React.CSSProperties = {
  background: 'transparent',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text-muted)',
  cursor: 'pointer',
  fontSize: 12,
  lineHeight: 1,
  padding: '3px 7px',
};

export function TaskCard({ task, onChangeStatus, onRemove }: Props) {
  const [busy, setBusy] = useState(false);

  const index = ORDER.indexOf(task.status);
  const prev = index > 0 ? ORDER[index - 1] : null;
  const next = index < ORDER.length - 1 ? ORDER[index + 1] : null;

  async function run(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        background: 'var(--color-surface-raised)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-3)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
        opacity: busy ? 0.5 : 1,
        transition: 'opacity 120ms ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {/* Первые 8 символов UUID — как короткий хеш коммита. Полный UUID
            занял бы всю карточку, а для визуального различения задач хватает
            префикса. Полное значение доступно через title при наведении. */}
        <span
          className="mono"
          style={{ fontSize: 11, color: 'var(--color-text-muted)' }}
          title={task.id}
        >
          {task.id.slice(0, 8)}
        </span>
        <button
          type="button"
          aria-label={`Удалить задачу ${task.title}`}
          onClick={() => run(() => onRemove(task.id))}
          disabled={busy}
          style={{ ...iconButton, borderColor: 'transparent' }}
        >
          ×
        </button>
      </div>

      <span style={{ fontSize: 13, fontWeight: 500 }}>{task.title}</span>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {task.assignee ? `@${task.assignee}` : '—'}
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            type="button"
            aria-label={`Вернуть назад: ${task.title}`}
            onClick={() => prev && run(() => onChangeStatus(task.id, prev))}
            disabled={busy || !prev}
            style={{ ...iconButton, opacity: prev ? 1 : 0.3 }}
          >
            ←
          </button>
          <button
            type="button"
            aria-label={`Продвинуть вперёд: ${task.title}`}
            onClick={() => next && run(() => onChangeStatus(task.id, next))}
            disabled={busy || !next}
            style={{ ...iconButton, opacity: next ? 1 : 0.3 }}
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
