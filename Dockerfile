FROM node:22-slim AS ui

WORKDIR /ui

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

RUN mkdir -p /ui/public && \
    cp -r ./node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/. /ui/public/


FROM python:3.13-slim AS app

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx ca-certificates && \
    rm -f /etc/nginx/sites-enabled/default && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY paas_web_app ./paas_web_app
COPY main.py README.md ./
COPY nginx.conf.template /app/nginx.conf.template
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

RUN uv sync --frozen --no-dev

COPY --from=ui /ui/public ./public

EXPOSE 80
CMD ["./start.sh"]
