import { MOCK_TASKS, type Task, type TaskStatus } from '../api/tasks';

const COLUMNS: { key: TaskStatus; label: string; accent: string }[] = [
  { key: 'todo', label: 'To do', accent: 'var(--color-text-muted)' },
  { key: 'in_progress', label: 'In progress', accent: 'var(--color-warn)' },
  { key: 'done', label: 'Done', accent: 'var(--color-success)' },
];

function TaskCard({ task }: { task: Task }) {
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
      }}
    >
      <span className="mono" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
        {task.id}
      </span>
      <span style={{ fontSize: 13, fontWeight: 500 }}>{task.title}</span>
      <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>@{task.assignee}</span>
    </div>
  );
}

export function TaskBoard() {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, minmax(220px, 1fr))',
        gap: 'var(--space-4)',
        alignItems: 'start',
      }}
    >
      {COLUMNS.map((col) => {
        const items = MOCK_TASKS.filter((t) => t.status === col.key);
        return (
          <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: col.accent }} />
              <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--color-text-muted)' }}>
                {col.label}
              </h3>
              <span className="mono" style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                {items.length}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {items.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
