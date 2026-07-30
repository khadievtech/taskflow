import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('открывается в режиме входа', () => {
    render(<LoginForm onSignIn={vi.fn()} onSignUp={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Войти' })).toBeInTheDocument();
  });

  it('блокирует отправку при пустых полях', () => {
    render(<LoginForm onSignIn={vi.fn()} onSignUp={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Войти' })).toBeDisabled();
  });

  it('вызывает вход с введёнными данными', async () => {
    const onSignIn = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSignIn={onSignIn} onSignUp={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Email'), '  me@example.com  ');
    await userEvent.type(screen.getByLabelText('Пароль'), 'secret-password');
    await userEvent.click(screen.getByRole('button', { name: 'Войти' }));

    // Email обрезается от пробелов, пароль — нет: пробел может быть его частью.
    expect(onSignIn).toHaveBeenCalledWith({
      email: 'me@example.com',
      password: 'secret-password',
    });
  });

  it('переключается в режим регистрации', async () => {
    render(<LoginForm onSignIn={vi.fn()} onSignUp={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: /Нет аккаунта/ }));
    expect(screen.getByRole('button', { name: 'Зарегистрироваться' })).toBeInTheDocument();
  });

  it('в режиме регистрации требует пароль от 8 символов', async () => {
    render(<LoginForm onSignIn={vi.fn()} onSignUp={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: /Нет аккаунта/ }));

    await userEvent.type(screen.getByLabelText('Email'), 'me@example.com');
    await userEvent.type(screen.getByLabelText('Пароль'), 'short');

    expect(screen.getByText('Минимум 8 символов')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Зарегистрироваться' })).toBeDisabled();
  });

  it('в режиме входа короткий пароль не блокируется', async () => {
    // При входе длину не проверяем: у пользователя может быть старый пароль,
    // созданный до введения требования. Отказ на клиенте не дал бы ему войти
    // вообще, хотя сервер такой пароль принимает.
    render(<LoginForm onSignIn={vi.fn()} onSignUp={vi.fn()} />);
    await userEvent.type(screen.getByLabelText('Email'), 'me@example.com');
    await userEvent.type(screen.getByLabelText('Пароль'), 'old');

    expect(screen.queryByText('Минимум 8 символов')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Войти' })).toBeEnabled();
  });

  it('вызывает регистрацию в соответствующем режиме', async () => {
    const onSignUp = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSignIn={vi.fn()} onSignUp={onSignUp} />);

    await userEvent.click(screen.getByRole('button', { name: /Нет аккаунта/ }));
    await userEvent.type(screen.getByLabelText('Email'), 'new@example.com');
    await userEvent.type(screen.getByLabelText('Пароль'), 'long-enough-password');
    await userEvent.click(screen.getByRole('button', { name: 'Зарегистрироваться' }));

    expect(onSignUp).toHaveBeenCalledWith({
      email: 'new@example.com',
      password: 'long-enough-password',
    });
  });

  it('показывает сообщение сервера при ошибке', async () => {
    const onSignIn = vi.fn().mockRejectedValue(new Error('Неверный email или пароль'));
    render(<LoginForm onSignIn={onSignIn} onSignUp={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Email'), 'me@example.com');
    await userEvent.type(screen.getByLabelText('Пароль'), 'wrong-password');
    await userEvent.click(screen.getByRole('button', { name: 'Войти' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Неверный email или пароль');
  });

  it('очищает ошибку при переключении режима', async () => {
    const onSignIn = vi.fn().mockRejectedValue(new Error('Неверный email или пароль'));
    render(<LoginForm onSignIn={onSignIn} onSignUp={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Email'), 'me@example.com');
    await userEvent.type(screen.getByLabelText('Пароль'), 'wrong-password');
    await userEvent.click(screen.getByRole('button', { name: 'Войти' }));
    expect(await screen.findByRole('alert')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Нет аккаунта/ }));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
