FROM node:24-alpine AS base
RUN corepack enable && corepack prepare pnpm@11.15.1 --activate

FROM base AS deps
WORKDIR /app
# pnpm-workspace.yaml carries the allowBuilds approvals; without it native binaries don't install.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# A private registry token goes in a user-level npmrc, removed in the same layer. pnpm ignores
# env-var expansion in a project .npmrc's credentials. Add `.npmrc` to the COPY above once the
# app depends on a private scope.
RUN --mount=type=secret,id=gh_token,required=false \
    if [ -f /run/secrets/gh_token ]; then \
      printf '//npm.pkg.github.com/:_authToken=%s\n' "$(cat /run/secrets/gh_token)" > /root/.npmrc; \
    fi && \
    pnpm install --frozen-lockfile && \
    rm -f /root/.npmrc

FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# No build args, and none are coming: every value is read server-side at request time, so the
# image is identical in every environment.
ENV CI=true
RUN pnpm --config.verify-deps-before-run=false build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
