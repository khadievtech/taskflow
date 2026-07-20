# TaskFlow Frontend

React + Vite + TypeScript. На Phase 0 — статичная Kanban-доска (mock-данные)
и живой статус подключения к backend.

## Локальный запуск

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Откроется на http://localhost:5173. Чтобы увидеть `backend: connected`,
backend должен быть запущен на http://localhost:8000 (см. `../backend/README.md`).

## Структура

```
src/
├── api/
│   ├── client.ts    # обёртка над fetch, единая точка конфигурации API_URL
│   └── tasks.ts      # типы + mock-данные (заменится реальным API на Phase 1)
├── components/
│   ├── StatusPanel.tsx  # живой пинг backend health-check
│   └── TaskBoard.tsx    # Kanban-доска
├── styles/tokens.css     # design tokens (цвета, типографика, spacing)
└── App.tsx
```
