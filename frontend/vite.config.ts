import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Прокси в dev-режиме повторяет то, что в production делает nginx:
    // запросы к /api/... уходят на backend, всё остальное отдаёт Vite.
    //
    // Зачем это нужно: без прокси в разработке фронтенд обращался бы к
    // http://localhost:8000 напрямую, то есть на другой origin — со всеми
    // вытекающими (CORS, адрес backend внутри бандла). С прокси dev и prod
    // ведут себя одинаково, и один класс расхождений между окружениями
    // исчезает совсем.
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
