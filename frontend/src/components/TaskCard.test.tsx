import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { Task } from '../api/tasks';
import { TaskCard } from './TaskCard';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: '11111111-2222-3333-4444-555555555555',
    title: 'Настроить мониторинг',
    description: null,
    status: 'todo',
    assignee: 'you',
    created_at: '2026-07-30T10:00:00Z',
    updated_at: '2026-07-30T10:00:00Z',
    ...overrides,
  };
}

describe('TaskCard', () => {
  it('показывает короткий префикс идентификатора, а не весь UUID', () => {
    render(<TaskCard task={makeTask()} onChangeStatus={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByText('11111111')).toBeInTheDocument();
    expect(screen.queryByText(makeTask().id)).not.toBeInTheDocument();
  });

  it('в статусе todo нельзя двинуться назад', () => {
    render(<TaskCard task={makeTask({ status: 'todo' })} onChangeStatus={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByLabelText(/Вернуть назад/)).toBeDisabled();
    expect(screen.getByLabelText(/Продвинуть вперёд/)).toBeEnabled();
  });

  it('в статусе done нельзя двинуться вперёд', () => {
    render(<TaskCard task={makeTask({ status: 'done' })} onChangeStatus={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByLabelText(/Продвинуть вперёд/)).toBeDisabled();
    expect(screen.getByLabelText(/Вернуть назад/)).toBeEnabled();
  });

  it('продвигает статус по порядку todo → in_progress', async () => {
    const onChangeStatus = vi.fn().mockResolvedValue(undefined);
    const task = makeTask({ status: 'todo' });
    render(<TaskCard task={task} onChangeStatus={onChangeStatus} onRemove={vi.fn()} />);

    await userEvent.click(screen.getByLabelText(/Продвинуть вперёд/));
    expect(onChangeStatus).toHaveBeenCalledWith(task.id, 'in_progress');
  });

  it('возвращает статус по порядку done → in_progress', async () => {
    const onChangeStatus = vi.fn().mockResolvedValue(undefined);
    const task = makeTask({ status: 'done' });
    render(<TaskCard task={task} onChangeStatus={onChangeStatus} onRemove={vi.fn()} />);

    await userEvent.click(screen.getByLabelText(/Вернуть назад/));
    expect(onChangeStatus).toHaveBeenCalledWith(task.id, 'in_progress');
  });

  it('вызывает удаление с идентификатором задачи', async () => {
    const onRemove = vi.fn().mockResolvedValue(undefined);
    const task = makeTask();
    render(<TaskCard task={task} onChangeStatus={vi.fn()} onRemove={onRemove} />);

    await userEvent.click(screen.getByLabelText(/Удалить задачу/));
    expect(onRemove).toHaveBeenCalledWith(task.id);
  });

  it('показывает прочерк, если исполнитель не назначен', () => {
    render(<TaskCard task={makeTask({ assignee: null })} onChangeStatus={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
