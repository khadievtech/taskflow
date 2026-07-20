# syntax=docker/dockerfile:1

FROM node:22-slim AS base
WORKDIR /app


# ---------------------------------------------------------------------------
# dev — используется в docker-compose.yml. Код перекрывается bind-mount'ом,
# поэтому здесь npm install ставит зависимости, а реальные исходники
# приедут из volume в compose (см. комментарий там же про node_modules).
# ---------------------------------------------------------------------------
FROM base AS dev
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ---------------------------------------------------------------------------
# build — компилирует статику. Отдельный от dev таргет, чтобы production-образ
# не тащил за собой vite dev-server и devDependencies.
# ---------------------------------------------------------------------------
FROM base AS build
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build


# ---------------------------------------------------------------------------
# production — Nginx отдаёт статические файлы. Пригодится в Phase 3
# (сборка образа в CI, публикация в GHCR, деплой на домашний сервер).
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80 || exit 1
