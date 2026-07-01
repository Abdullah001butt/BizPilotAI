# syntax=docker/dockerfile:1
# ─────────────────────────── Build stage ────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies with a clean, reproducible install from the lockfile.
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# The API base URL is baked in at build time; nginx proxies /api to the backend.
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# ─────────────────────────── Runtime stage ──────────────────────────────────
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
