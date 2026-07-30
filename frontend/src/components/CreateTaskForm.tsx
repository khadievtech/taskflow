import { useState } from 'react';
import type { TaskCreate } from '../api/tasks';

interface Props {
  onCreate: (data: TaskCreate) => Promise<void>;
}

const inputStyle: React.CSSProperties = {
  background: 'var(--color-surface-raised)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text)',
  padding: '8px 10px',
  fontSize: 13,
  fontFamily: 'inherit',
};

export function CreateTaskForm({ onCreate }: Props) {
  const [title, setTitle] = useState('');
  const [assignee, setAssignee] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = title.trim();
  // Ограничение 200 символов повторяет max_length в схеме TaskCreate на
  // бэкенде. Валидация на клиенте не заменяет серверную (её обходят через
  // curl), а лишь избавляет пользователя от лишнего запроса.
  const invalid = trimmed.length === 0 || trimmed.length > 200;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (invalid || busy) return;

    setBusy(true);
    setError(null);
    try {
      await onCreate({ title: trimmed, assignee: assignee.trim() || null });
      setTitle('');
      setAssignee('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось создать задачу');
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}
    >
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        <input
          aria-label="Название задачи"
          placeholder="Что нужно сделать?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={200}
          disabled={busy}
          style={{ ...inputStyle, flex: '1 1 260px' }}
        />
        <input
          aria-label="Исполнитель"
          placeholder="Исполнитель"
          value={assignee}
          onChange={(e) => setAssignee(e.target.value)}
          maxLength={100}
          disabled={busy}
          style={{ ...inputStyle, flex: '0 1 140px' }}
        />
        <button
          type="submit"
          disabled={invalid || busy}
          style={{
            background: invalid || busy ? 'var(--color-surface-raised)' : 'var(--color-accent)',
            color: invalid || busy ? 'var(--color-text-muted)' : '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 16px',
            fontSize: 13,
            fontWeight: 500,
            cursor: invalid || busy ? 'not-allowed' : 'pointer',
          }}
        >
          {busy ? 'Создаём…' : 'Добавить'}
        </button>
      </div>

      {error && (
        <span role="alert" style={{ fontSize: 12, color: '#e5484d' }}>
          {error}
        </span>
      )}
    </form>
  );
}
