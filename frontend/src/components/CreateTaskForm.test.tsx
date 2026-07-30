import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { CreateTaskForm } from './CreateTaskForm';

describe('CreateTaskForm', () => {
  it('блокирует отправку, пока название пусто', () => {
    render(<CreateTaskForm onCreate={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Добавить' })).toBeDisabled();
  });

  it('блокирует отправку, если название состоит из пробелов', async () => {
    render(<CreateTaskForm onCreate={vi.fn()} />);
    await userEvent.type(screen.getByLabelText('Название задачи'), '   ');
    expect(screen.getByRole('button', { name: 'Добавить' })).toBeDisabled();
  });

  it('передаёт название без лишних пробелов и очищает поля', async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<CreateTaskForm onCreate={onCreate} />);

    await userEvent.type(screen.getByLabelText('Название задачи'), '  Настроить TLS  ');
    await userEvent.type(screen.getByLabelText('Исполнитель'), 'you');
    await userEvent.click(screen.getByRole('button', { name: 'Добавить' }));

    expect(onCreate).toHaveBeenCalledWith({ title: 'Настроить TLS', assignee: 'you' });
    expect(screen.getByLabelText('Название задачи')).toHaveValue('');
  });

  it('передаёт null вместо пустого исполнителя', async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<CreateTaskForm onCreate={onCreate} />);

    await userEvent.type(screen.getByLabelText('Название задачи'), 'Задача');
    await userEvent.click(screen.getByRole('button', { name: 'Добавить' }));

    expect(onCreate).toHaveBeenCalledWith({ title: 'Задача', assignee: null });
  });

  it('показывает ошибку и не очищает поля, если запрос упал', async () => {
    const onCreate = vi.fn().mockRejectedValue(new Error('База недоступна'));
    render(<CreateTaskForm onCreate={onCreate} />);

    await userEvent.type(screen.getByLabelText('Название задачи'), 'Задача');
    await userEvent.click(screen.getByRole('button', { name: 'Добавить' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('База недоступна');
    // Введённое не должно пропасть: пользователю нужно повторить попытку,
    // а не набирать текст заново.
    expect(screen.getByLabelText('Название задачи')).toHaveValue('Задача');
  });
});
