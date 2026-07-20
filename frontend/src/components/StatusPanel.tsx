import { useEffect, useState } from 'react';
import { API_URL, checkBackendHealth } from '../api/client';

type ConnectionState = 'checking' | 'online' | 'offline';

const POLL_INTERVAL_MS = 10_000;

export function StatusPanel() {
  const [state, setState] = useState<ConnectionState>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const result = await checkBackendHealth();
      if (cancelled) return;
      setState(result.status === 'ok' ? 'online' : 'offline');
      setLastChecked(new Date());
    }

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const dotColor =
    state === 'online'
      ? 'var(--color-success)'
      : state === 'offline'
        ? '#e5484d'
        : 'var(--color-text-muted)';

  const label =
    state === 'online' ? 'backend: connected' : state === 'offline' ? 'backend: unreachable' : 'backend: checking...';

  return (
    <div
      className="mono"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
        padding: 'var(--space-2) var(--space-4)',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-sm)',
        fontSize: 12,
        color: 'var(--color-text-muted)',
      }}
      role="status"
      aria-live="polite"
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: dotColor,
          flexShrink: 0,
        }}
        aria-hidden
      />
      <span>{label}</span>
      <span style={{ opacity: 0.5 }}>·</span>
      <span style={{ opacity: 0.7 }}>{API_URL}</span>
      {lastChecked && (
        <>
          <span style={{ opacity: 0.5 }}>·</span>
          <span style={{ opacity: 0.7 }}>{lastChecked.toLocaleTimeString()}</span>
        </>
      )}
    </div>
  );
}
