### Hexlet tests and linter status:
[![Actions Status](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions)
[![CI](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml/badge.svg)](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml)

## Описание

Сервис сокращения ссылок: **Flask** + **SQLModel** + **PostgreSQL**.

В продакшене (Render) UI раздаётся через **Nginx**, запросы к API проксируются на бэкенд внутри одного контейнера. При старте приложения таблицы в БД создаются автоматически.

## Развернутое приложение

**URL:** https://devops-engineer-from-scratch-project-313-6ccf.onrender.com

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/ping` | Проверка работоспособности |
| GET | `/api/links` | Список ссылок (пагинация: `?range=[0,10]`) |
| POST | `/api/links` | Создание ссылки |
| GET | `/api/links/:id` | Получение ссылки |
| PUT | `/api/links/:id` | Обновление ссылки |
| DELETE | `/api/links/:id` | Удаление ссылки |

### Примеры

```bash
curl https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/ping

curl "https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/api/links?range=[0,10]"

curl -X POST https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/api/links \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/long-url", "short_name": "exmpl"}'
```

## Локальный запуск

### Требования

- [uv](https://docs.astral.sh/uv/)
- Python 3.13+
- PostgreSQL
- Node.js 22+ (для UI в режиме разработки)

### Переменные окружения

Файл `.env` в корне проекта (не коммитится):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/appdb
BASE_URL=http://localhost:8080
PORT=8080
SENTRY_DSN=https://your-sentry-dsn
```

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Подключение к PostgreSQL (**обязательно**) |
| `BASE_URL` | Базовый URL для поля `short_url` |
| `PORT` | Порт бэкенда (по умолчанию `8080`) |
| `SENTRY_DSN` | DSN Sentry (опционально) |

### Установка и запуск бэкенда

```bash
make install
make run
```

Проверка:

```bash
curl http://localhost:8080/ping
```

### UI + API (режим разработки)

```bash
make dev FRAMEWORK=flask
```

- UI: http://localhost:5173
- API: http://localhost:8080

## Разработка

### Конфигурация и CI

| Команда | Назначение |
|---------|------------|
| `make setup` | Установка зависимостей в CI (без `.venv`) |
| `make install` | Установка зависимостей локально (с `.venv`) |
| `make lint` | Ruff (`ruff.toml`) |
| `make test` | Pytest (`tests/`) |
| `make build` | Сборка wheel |
| `make dev FRAMEWORK=flask` | Параллельный запуск UI и API |

### Docker (prod-like)

Nginx + UI + API в одном контейнере:

```bash
docker build -t paas-web-app .
docker run --rm -p 8080:80 --env-file .env paas-web-app
```

## Структура проекта

- Точка входа: `main.py` (экспорт `app`)
- Приложение: `paas_web_app/`
- Тесты: `tests/`
- Линтер: `ruff.toml`
- CI: `.github/workflows/` (`hexlet-check`, `ci`)
