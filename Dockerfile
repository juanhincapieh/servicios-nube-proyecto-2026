# syntax=docker/dockerfile:1

# ---- Etapa 1: build ----
FROM node:20-alpine AS builder
WORKDIR /app

# Instalar dependencias (incluye devDependencies para poder compilar)
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el resto del codigo y compilar.
COPY . .
RUN npx next build

# ---- Etapa 2: runtime ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Solo dependencias de produccion + artefactos ya compilados
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

# Binario para la prueba de stress (Punto 5). stress-ng acepta las mismas
# flags que usa la app (--cpu/--io/--vm/--vm-bytes/--timeout).
# Se invoca con STRESS_PATH=/usr/bin/stress-ng
RUN apk add --no-cache stress-ng

# Ejecutar como usuario sin privilegios (mejor practica de seguridad)
USER node

EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]
