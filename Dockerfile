FROM python:3.13-slim

WORKDIR /app

# Установка менеджера пакетов uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Копирование описания зависимостей
COPY pyproject.toml uv.lock ./

# Сборка: установка зависимостей (без dev-группы)
RUN uv sync --frozen --no-dev --no-install-project

# Копирование исходного кода приложения (README.md нужен hatchling при сборке)
COPY paas_web_app ./paas_web_app
COPY main.py README.md ./

# Установка проекта в виртуальное окружение
RUN uv sync --frozen --no-dev

EXPOSE 8080

# Запуск Flask-приложения на порту 8080
CMD ["uv", "run", "python", "main.py"]
