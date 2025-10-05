# Stage 1: Dependencies
FROM node:22-alpine AS deps
RUN apk add --no-cache libc6-compat

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Install deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:22-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Bring node_modules and source
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate Prisma Client (ensures Query Engine for alpine and types are in build)
RUN npx prisma generate

# Build Next.js standalone output
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# Stage 3: Runner
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

# Copy production artifacts
# Standalone server and node_modules subset
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# Next.js static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# Prisma schema and migrations (required for migrate deploy)
COPY --from=builder --chown=nextjs:nodejs /app/prisma ./prisma

# Caches and uploads directories
RUN mkdir -p .next/cache && chown -R nextjs:nodejs .next \
  && mkdir -p public/uploads && chown -R nextjs:nodejs public/uploads

# Ensure Prisma CLI is available at runtime:
# - If @prisma/cli is a devDependency, prefer using npx which downloads a temp binary.
# - If you want faster startup and offline, add prisma as a production dependency.
# Using npx here to avoid inflating image size.
USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Apply DB migrations on startup, then start the server
# Requires DATABASE_URL to be provided at runtime.
CMD ["sh", "-c", "npx --yes prisma migrate deploy && node server.js"]
